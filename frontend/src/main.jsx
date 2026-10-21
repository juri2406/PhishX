import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';
import LiveChecks from './LiveChecks';
import evaluationReportUrl from '../../docs/evaluation-run06.md?url';
import neuralReportUrl from '../../docs/person1-neural-handoff.md?url';
import releaseReportUrl from '../../docs/project-completion.md?url';

const examples = [
  ['Low sample', 'https://example.com/'],
  ['High sample', 'https://account-check.example/login'],
  ['Synthetic lookalike', 'https://раypal.example/login'],
  ['Encoded sample', 'https://example.com/%6c%6f%67%69%6e'],
];
const base = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '');
const modelExamples = [
  ['Official domain', 'https://github.com/'],
  ['Synthetic lookalike', 'https://pаypal.com/login'],
  ['Synthetic subdomain', 'https://paypal.account-check.example/login'],
  ['Encoded path', 'https://example.com/%6c%6f%67%69%6e'],
];

function App() {
  const [url, setUrl] = useState('');
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const resultRef = useRef(null);
  async function checkHealth() {
    try {
      const response = await fetch(`${base}/health`, {signal: AbortSignal.timeout(5000)});
      if (!response.ok) throw new Error();
      setHealth(await response.json()); setHealthError('');
    } catch {setHealth(null); setHealthError('Backend unreachable. Start the API, then retry.');}
  }
  useEffect(() => {checkHealth();}, []);
  useEffect(() => {if (result) resultRef.current?.focus();}, [result]);
  async function scan(event) {
    event.preventDefault(); setError(''); setResult(null); setBusy(true);
    try {
      const response = await fetch(`${base}/scan`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url}), signal:AbortSignal.timeout(30000)});
      let data;
      try {data = await response.json();}
      catch {throw new Error('The API returned an unreadable response. Check the backend and retry.');}
      if (!response.ok) throw new Error(data.error?.message || 'Scan failed. Retry after checking the API.');
      setResult(data);
    } catch (e) {setError(e.name === 'TimeoutError' ? 'The scan timed out. Retry or check the backend logs.' : e.message === 'Failed to fetch' ? 'Cannot reach the API. Check that the backend is running.' : e.message);}
    finally {setBusy(false);}
  }
  return <div className="shell">
    <header className="flex items-center justify-between gap-4"><a className="brand" href="/" aria-label="PhishX home"><svg width="28" height="32" viewBox="0 0 28 32" fill="none" aria-hidden="true"><path d="M14 2 26 7v9c0 7-7 12-12 14C9 28 2 23 2 16V7Z" stroke="currentColor" strokeWidth="2"/><path d="m8 16 4 4 8-9" stroke="currentColor" strokeWidth="2"/></svg>PhishX</a><span className="prototype">Local prototype</span></header>
    <main>
      <div className="intro"><h1>Inspect a link.<br/>Understand its risk.</h1><p>Analyze URL signals and see the reasons behind the model’s prediction. The model analyzes URL text. After a scan, you can choose to run separate live domain checks.</p></div>
      <div className="workspace">
        <section className="scanner" aria-labelledby="scanner-title">
          <div className="section-title"><h2 id="scanner-title">URL scanner</h2><span className={`status ${health?.ready ? 'online' : ''}`}>{health?.ready ? health.mode === 'fixture' ? 'Fixture API ready' : 'Model API ready' : 'API not ready'}</span></div>
          {healthError && <div className="notice" role="status">{healthError} <button type="button" onClick={checkHealth}>Retry connection</button></div>}
          {health?.cascade_status === 'available' && <div className="notice">{health.model_notice || 'Research cascade: false positives worsened on broader-source testing. Neural explanations are unavailable. Use the classical provider for the established demo.'}</div>}
          {health?.mode === 'fixture' && <div className="notice">Fixture mode: the four examples return illustrative sample scores. They are not measured predictions.</div>}
          {health?.mode === 'model' && !health.ready && <div className="notice">Waiting for Person 1’s model. Start the API in fixture mode to work on the demo.</div>}
          <form onSubmit={scan}>
            <label htmlFor="url">URL to analyze</label>
            <input id="url" type="text" inputMode="url" autoComplete="off" spellCheck="false" placeholder="https://example.com/" maxLength={2048} required value={url} onChange={e => {setUrl(e.target.value);setResult(null);setError('');}} aria-describedby="url-hint" disabled={busy}/>
            <p id="url-hint" className="hint">Include http:// or https://. Maximum 2,048 characters.</p>
            <button className="primary" type="submit" disabled={busy || !url}>{busy ? 'Analyzing URL…' : 'Analyze URL'}<span aria-hidden="true">→</span></button>
          </form>
          <div className="examples"><p>{health?.mode === 'fixture' ? 'Try a fixture example' : 'Try a URL text example'}</p>{health?.mode === 'model' && <p className="hint">Synthetic examples test URL patterns; they are not verified phishing pages.</p>}<div className="flex flex-wrap gap-2">{(health?.mode === 'fixture' ? examples : modelExamples).map(([label,value]) => <button type="button" key={label} disabled={busy} onClick={() => {setUrl(value);setError('');setResult(null);}}>{label}</button>)}</div></div>
          {busy && <p className="feedback" role="status">Waiting for the API response…</p>}
          {error && <p className="error" role="alert">{error}</p>}
        </section>
        <aside className="scope"><h2>What this prototype covers</h2><p>The connected detection path, observed URL signals, and available model explanations.</p><dl><div><dt>Model path</dt><dd>{health?.model_profile === 'release_cascade' ? 'RF + Char-CNN' : health?.cascade_status === 'available' ? 'Research cascade' : 'Classical'}</dd></div><div><dt>Char-CNN cascade</dt><dd>{health?.cascade_status === 'available' ? 'Connected' : 'Not connected'}</dd></div><div><dt>Live domain checks</dt><dd>{health?.live_signals_enabled ? 'Optional' : 'Disabled'}</dd></div></dl><p className="hint">A low score is not a guarantee of safety. HTTPS alone does not establish certificate validity.</p></aside>
      </div>
      {result ? <section className="results" ref={resultRef} tabIndex={-1} aria-labelledby="result-title">
        <div className="result-head"><div><h2 id="result-title">{result.mode === 'fixture' ? 'Fixture result' : 'Scan result'}</h2><p className="host">{result.normalized_host}</p></div><div className={`score ${result.risk_level.toLowerCase()}`}><strong>{result.risk_score}<small>/100</small></strong><span>{result.risk_level} risk{result.mode === 'fixture' ? ' · sample' : ''}</span></div></div>
        <p className="score-note">{result.mode === 'fixture' ? 'Illustrative sample response. No model ran for this URL.' : result.probability_calibrated ? 'Calibrated model probability.' : 'Model score; probability calibration has not been verified.'} Phishing output: {(result.phishing_probability*100).toFixed(1)}%.</p>
        <div className="result-grid"><div><h3>Model contributions</h3>{result.explanation_audit && <p>Exact URL-component Shapley values for the complete cascade, relative to {result.explanation_audit.reference_url}. Signed contributions and the additivity check are included in the API response. These explain the detector, not the safety of the site.</p>}{result.explanation_audit ? <dl className="details">{Object.entries(result.explanation_audit.contributions).map(([name,value]) => <div key={name}><dt>{{url_scheme:'Protocol',url_authority:'Host',url_path:'Path',url_query:'Query'}[name] || name}</dt><dd>{value > 0 ? '+' : ''}{value.toFixed(4)}</dd></div>)}</dl> : result.explanation_items.length > 0 ? <ol className="reasons">{result.explanation_items.map(item => <li key={item.feature}><p>{item.reason}</p><span>{item.feature}: {String(item.observed_value)} · +{item.contribution.toPrecision(3)} ({result.explanation_scale})</span></li>)}</ol> : <p>{result.explanation_message || 'No features made a positive contribution to the phishing output.'}</p>}<h3>Observed URL features</h3>{result.observed_signals.length ? <ul className="signals">{result.observed_signals.map(item => <li key={item.name}><strong>{item.name.replaceAll('_',' ')}: {String(item.value)}</strong><p>{item.description}</p></li>)}</ul> : <p>No observed signals returned.</p>}</div><div><h3>Closest registry brand</h3><p>{result.matched_brand || 'No brand match reported.'}</p><p>Similarity comparison only; this does not identify the site’s owner.</p>{result.skeleton_distance !== null && <p>Skeleton distance: {result.skeleton_distance}</p>}<h3>Outside the text model</h3><p>{result.unavailable_signals.join(' · ')}</p><p>These signals do not enter this prediction. Request current observations in Live domain checks below.</p><h3>Run details</h3><dl className="details"><div><dt>Model</dt><dd>{result.model_used}</dd></div><div><dt>Version</dt><dd>{result.model_version}</dd></div><div><dt>Cascade</dt><dd>{result.cascade_status}</dd></div><div><dt>Inference</dt><dd>{result.timings_ms.inference} ms</dd></div><div><dt>Explanation</dt><dd>{result.timings_ms.explanation} ms</dd></div></dl></div></div>
        <LiveChecks key={result.submitted_url} url={result.submitted_url} enabled={health?.live_signals_enabled && result.mode === 'model'} base={base}/><details><summary>API response</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
      </section> : <section className="empty"><h2>Your analysis will appear here.</h2><p>Enter a URL above or choose a sample to test the scanner.</p></section>}
    </main><footer><span>PhishX · Research prototype</span><a href={health?.model_profile === 'release_cascade' ? releaseReportUrl : health?.cascade_status === 'available' ? neuralReportUrl : evaluationReportUrl} target="_blank" rel="noreferrer">Evaluation report and known limitations</a></footer>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
