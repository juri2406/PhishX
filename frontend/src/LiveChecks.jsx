import React, {useState} from 'react';

export default function LiveChecks({url, enabled, base}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  async function check() {
    setBusy(true); setError(''); setResult(null);
    try {
      const response = await fetch(`${base}/signals`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url}), signal:AbortSignal.timeout(15000)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || 'Live checks failed. Retry shortly.');
      setResult(data);
    } catch (e) {
      setError(e.name === 'TimeoutError' ? 'Live checks timed out. You can retry; your model result is unchanged.' : e.message === 'Failed to fetch' ? 'Cannot reach the backend. Check the connection and retry.' : e.message);
    } finally {setBusy(false);}
  }
  return <section className="live-checks" aria-labelledby="live-title">
    <h3 id="live-title">Live domain checks</h3>
    <p>Optional checks contact the target server and registration services. Only headers are requested from the target; page content is not analyzed. These observations do not change the model score.</p>
    {enabled ? <button className="live-button" type="button" disabled={busy} onClick={check}>{busy ? 'Checking domain…' : result ? 'Refresh live checks' : 'Run live checks'}</button> : <p>Live checks are disabled on this backend.</p>}
    {busy && <p role="status">Checking DNS, TLS, redirects and registration data…</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {result && <div role="status"><ul className="signals">{result.checks.map(item => <li key={item.name}><strong>{item.name}: {item.status}{item.value !== null && item.value !== undefined ? ` · ${String(item.value)}` : ''}</strong><p>{item.message}</p></li>)}</ul><p>Checked: {new Date(result.checked_at).toLocaleString()}. A successful check does not establish that a site is safe.</p>{result.redirect_chain.length > 0 && <details><summary>Observed redirect chain</summary><ol>{result.redirect_chain.map((hop, index) => <li key={index}>{hop.scheme}://{hop.host} · HTTP {hop.http_status}</li>)}</ol></details>}</div>}
  </section>;
}
