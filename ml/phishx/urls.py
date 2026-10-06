"""Conservative HTTP URL parsing. Never resolves or fetches submitted URLs."""
from dataclasses import dataclass, asdict
from urllib.parse import urlsplit, urlunsplit
import ipaddress
import re
import idna
import tldextract

# Packaged PSL snapshot; disable network access and the user cache.
_EXTRACT = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None,
                                include_psl_private_domains=True)
class InvalidURL(ValueError):
    pass

@dataclass(frozen=True)
class NormalizedURL:
    raw: str
    canonical: str
    scheme: str
    ascii_host: str
    unicode_host: str
    registrable_domain: str
    domain_label: str
    subdomain: str
    suffix: str
    path: str
    query: str
    is_ip: bool
    has_userinfo: bool
    explicit_scheme: bool

    def to_dict(self):
        return asdict(self)

def normalize_url(value: str) -> NormalizedURL:
    if not isinstance(value, str) or not value.strip():
        raise InvalidURL("Enter a non-empty URL.")
    raw = value.strip()
    if len(raw) > 2048:
        raise InvalidURL("URL exceeds 2048 characters.")
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in raw) or '\\' in raw:
        raise InvalidURL("Whitespace, control characters and backslashes are unsupported.")
    if re.search(r'%(?![0-9a-fA-F]{2})', raw):
        raise InvalidURL("Malformed percent encoding.")
    explicit = bool(re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', raw))
    candidate = raw if explicit else 'https://' + raw
    try:
        parts = urlsplit(candidate)
        if parts.scheme.lower() not in ('http', 'https'):
            raise InvalidURL("Only HTTP and HTTPS URLs are supported.")
        host = parts.hostname
        port = parts.port
        if not host:
            raise InvalidURL("URL must contain a hostname.")
        host = host.rstrip('.').lower()
        try:
            ipaddress.ip_address(host)
            is_ip = True; ascii_host = unicode_host = host
        except ValueError:
            is_ip = False
            ascii_host = idna.encode(host, uts46=True, transitional=False).decode('ascii')
            unicode_host = idna.decode(ascii_host)
        if not is_ip and ('.' not in ascii_host or len(ascii_host) > 253):
            raise InvalidURL("Use a fully qualified hostname or an IP address.")
        extracted = _EXTRACT(ascii_host) if not is_ip else None
        # Unknown suffixes use the final two labels for grouping; documented limitation.
        if extracted and extracted.suffix and extracted.domain:
            registered = extracted.top_domain_under_public_suffix
            domain_label = idna.decode(extracted.domain)
            subdomain = extracted.subdomain; suffix = extracted.suffix
        elif extracted and extracted.suffix:
            # The host itself is a PSL suffix (e.g. s3.amazonaws.com).
            # Path-hosted URLs are valid; conservatively group the entire host.
            registered = ascii_host; domain_label = idna.decode(ascii_host.split('.')[0])
            subdomain = ''; suffix = extracted.suffix
        elif not is_ip:
            labels = ascii_host.split('.')
            registered = '.'.join(labels[-2:]); domain_label = idna.decode(labels[-2])
            subdomain = '.'.join(labels[:-2]); suffix = labels[-1]
        else:
            registered = ascii_host; domain_label = ascii_host; subdomain = suffix = ''
        authority = '[' + ascii_host + ']' if ':' in ascii_host else ascii_host
        if port is not None and not (parts.scheme == 'https' and port == 443 or parts.scheme == 'http' and port == 80):
            authority += ':' + str(port)
        # Preserve credentials in identity to avoid collapsing distinct training examples.
        if '@' in parts.netloc:
            authority = parts.netloc.rsplit('@', 1)[0] + '@' + authority
        canonical = urlunsplit((parts.scheme.lower(), authority, parts.path or '/', parts.query, ''))
        return NormalizedURL(raw, canonical, parts.scheme.lower(), ascii_host, unicode_host,
                             registered, domain_label, subdomain, suffix,
                             parts.path, parts.query, is_ip, '@' in parts.netloc, explicit)
    except (ValueError, idna.IDNAError) as exc:
        raise InvalidURL(str(exc)) from exc
