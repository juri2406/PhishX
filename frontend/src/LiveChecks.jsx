import React, {useState} from 'react';

function valueLabel(item) {
  if (item.value === null || item.value === undefined) return '';
  if (typeof item.value === 'boolean') return item.value ? 'Yes' : 'No';
  if (item.name === 'Domain age' && typeof item.value === 'number') return `${item.value.toLocaleString()} days`;
  return String(item.value);
}
export default function LiveChecks({url, enabled, base}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  async function check() {
    setBusy(true); setError(''); setResult(null);
    try {
      const response = await fetch(`${base}/signals`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url}), signal:AbortSignal.timeout(15000)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || 'Live checks couldn’t finish. Please try again.');
      setResult(data);
    } catch (e) {
      setError(e.name === 'TimeoutError' ? 'Live checks took too long. You can retry; your model score is unchanged.' : e.message === 'Failed to fetch' ? 'The scanner is disconnected. Check the connection and try again.' : e.message);
    } finally {setBusy(false);}
  }
  return <section className="live-checks" aria-labelledby="live-title" aria-busy={busy}>
    <div className="live-heading"><div><h3 id="live-title">Live domain checks <span className="optional-label">Optional</span></h3><p>Look up network and registration details. These checks contact the target website and registration services; they won’t change your score.</p></div>{enabled && <button className="live-button" type="button" disabled={busy} onClick={check}>{busy ? 'Checking domain…' : result ? 'Refresh live checks' : 'Run live checks'}</button>}</div>
    {!enabled && <p className="hint">Live checks are disabled on this backend.</p>}
    {busy && <p className="feedback" role="status">Checking DNS, the HTTPS certificate, redirects and registration data…</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {result && <><p className="live-status" role="status">{result.checks.length} checks returned. The model score is unchanged.</p><ul className="check-list">{result.checks.map(item => <li key={item.name}><div className="check-title"><strong>{item.name === 'TLS validity' ? 'HTTPS certificate' : item.name}</strong><span className={`check-state ${item.status === 'available' ? 'available' : ''}`}>{item.status.replaceAll('_',' ')}</span></div>{valueLabel(item) && <p className="check-value">{valueLabel(item)}</p>}<p>{item.message}</p></li>)}</ul><p className="hint">Checked {new Date(result.checked_at).toLocaleString()}. A successful check does not establish that a site is safe.</p></>}
    <details className="live-info"><summary>What do these checks look at?</summary><p>DNS, HTTPS certificate validity, redirect headers and RDAP registration data. Only headers are requested from the target; page content is not analyzed.</p>{result?.redirect_chain.length > 0 && <><h4>Observed redirect chain</h4><ol>{result.redirect_chain.map((hop, index) => <li key={index}>{hop.scheme}://{hop.host} · HTTP {hop.http_status}</li>)}</ol></>}</details>
  </section>;
}
