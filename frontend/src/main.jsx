import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';
import LiveChecks from './LiveChecks';
import evaluationReportUrl from '../../docs/evaluation-run06.md?url';
import neuralReportUrl from '../../docs/person1-neural-handoff.md?url';
import releaseReportUrl from '../../docs/project-completion.md?url';

const fixtureExamples = [
  ['Low sample', 'https://example.com/'],
  ['High sample', 'https://account-check.example/login'],
  ['Synthetic lookalike', 'https://раypal.example/login'],
  ['Encoded sample', 'https://example.com/%6c%6f%67%69%6e'],
];
const modelExamples = [
  ['Official site', 'https://github.com/'],
  ['Lookalike URL', 'https://pаypal.com/login'],
  ['Misleading subdomain', 'https://paypal.account-check.example/login'],
  ['Encoded path', 'https://example.com/%6c%6f%67%69%6e'],
];
const base = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '');
const componentNames = {url_scheme:'Link protocol', url_authority:'Website address', url_path:'Page path', url_query:'URL parameters'};
const riskCopy = {
  low: 'The model found fewer phishing signals in this link.',
  medium: 'The model found some patterns that deserve a closer look.',
  high: 'The model detected patterns associated with phishing.',
  critical: 'The model detected patterns strongly associated with phishing.',
};
const displayValue = value => typeof value === 'number' ? value.toLocaleString(undefined, {maximumFractionDigits:4}) : String(value);
function Icon({name, ...props}) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
    {name === 'shield' ? <><path d="m12 2 9 4v6c0 5-5 8-9 10-4-2-9-5-9-10V6Z"/><path d="m8 12 3 3 5-6"/></> : name === 'link' ? <><path d="m10 13 4-4"/><path d="m8 16-1 1a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0m2 10a4 4 0 0 0 6 0l4-4a4 4 0 0 0-6-6l-1 1" transform="translate(1 0)"/></> : <><path d="M4 12h16m-6-6 6 6-6 6"/></>}
  </svg>;
}
function Explanation({result}) {
  const audit = result.explanation_audit;
  return <details className="disclosure">
    <summary>What influenced this score?</summary>
    <div className="disclosure-body">
      {audit ? <><p>These values show how each part of the link changed the model’s output relative to the reference URL. Positive values raise it; negative values lower it.</p>
        <dl className="details contribution-list">{Object.entries(audit.contributions).map(([name,value]) => <div key={name}><dt>{componentNames[name] || name}</dt><dd>{value > 0 ? '+' : ''}{value.toFixed(4)}</dd></div>)}</dl>
        <p className="hint">Method: exact URL-component Shapley values for the full model. Reference: <code>{audit.reference_url}</code>, a placeholder, not a known-safe site. This explains the model, not the site’s safety.</p>
      </> : result.explanation_items.length ? <ol className="reasons">{result.explanation_items.map(item => <li key={item.feature}><p>{item.reason}</p><span>{item.feature}: {String(item.observed_value)} · +{item.contribution.toPrecision(3)} ({result.explanation_scale})</span></li>)}</ol> : <p>{result.explanation_message || 'No features made a positive contribution to the model’s phishing output.'}</p>}
    </div>
  </details>;
}
function ScanResult({result, health, resultRef}) {
  const level = result.risk_level.toLowerCase();
  return <section className="results" ref={resultRef} tabIndex={-1} aria-labelledby="result-title">
    <div className="result-head">
      <div><h2 id="result-title">{result.mode === 'fixture' ? 'Sample result' : 'Your link analysis'}</h2><p className="host">{result.normalized_host}</p><p className="result-description">{result.mode === 'fixture' ? 'An illustrative response for testing the interface. No model ran.' : riskCopy[level] || 'Review the model score and the observed link details below.'}</p></div>
      <div className={`score ${level}`}><span>{result.risk_level} model risk{result.mode === 'fixture' ? ' · sample' : ''}</span><strong>{result.risk_score}<small> / 100</small></strong></div>
    </div>
    <p className="score-note">{result.mode === 'fixture' ? 'Sample score only.' : result.probability_calibrated ? 'Calibrated model probability.' : 'An uncalibrated model score, not a verified probability of danger.'} A low score does not guarantee safety.</p>
    <LiveChecks key={result.submitted_url} url={result.submitted_url} enabled={health?.live_signals_enabled && result.mode === 'model'} base={base}/>
    <div className="result-disclosures">
      <Explanation result={result}/>
      <details className="disclosure"><summary>View observed link details <span className="summary-count">{result.observed_signals.length} signals</span></summary><div className="disclosure-body">
        <h3>Brand-name comparison</h3><p>{result.matched_brand ? <>Closest registry brand: <strong>{result.matched_brand}</strong>.</> : 'No brand match was reported.'} Similarity does not identify the website’s owner.</p>
        {result.skeleton_distance !== null && <p className="hint">Skeleton distance: {result.skeleton_distance}</p>}
        {result.observed_signals.length ? <ul className="signals">{result.observed_signals.map(item => <li key={item.name}><div><strong>{item.name.replaceAll('_',' ')}</strong><span className="signal-value">{displayValue(item.value)}</span></div><p>{item.description}</p></li>)}</ul> : <p>No observed signals were returned.</p>}
        <p className="hint">Outside the text model: {result.unavailable_signals.join(' · ')}. Live checks are separate observations and do not affect this score.</p>
      </div></details>
      <details className="disclosure"><summary>Model and technical details</summary><div className="disclosure-body"><dl className="details">
        <div><dt>Model</dt><dd>{result.model_used}</dd></div><div><dt>Version</dt><dd>{result.model_version}</dd></div><div><dt>Cascade</dt><dd>{result.cascade_status}</dd></div><div><dt>Phishing output</dt><dd>{(result.phishing_probability*100).toFixed(1)}%</dd></div><div><dt>Inference</dt><dd>{result.timings_ms.inference} ms</dd></div><div><dt>Explanation</dt><dd>{result.timings_ms.explanation} ms</dd></div>
      </dl></div></details>
      <details className="disclosure"><summary>View full API response</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
    </div>
  </section>;
}
function App() {
  const [url, setUrl] = useState('');
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [invalid, setInvalid] = useState(false);
  const [result, setResult] = useState(null);
  const resultRef = useRef(null);
  const inputRef = useRef(null);
  async function checkHealth() {
    try {
      const response = await fetch(`${base}/health`, {signal: AbortSignal.timeout(5000)});
      if (!response.ok) throw new Error();
      setHealth(await response.json()); setHealthError('');
    } catch {setHealth(null); setHealthError('We couldn’t connect to the scanner. Make sure the local API is running, then try again.');}
  }
  useEffect(() => {checkHealth();}, []);
  useEffect(() => {if (result) resultRef.current?.focus();}, [result]);
  useEffect(() => {if (error) inputRef.current?.focus();}, [error]);
  function changeUrl(value) {setUrl(value); setError(''); setInvalid(false); setResult(null);}
  async function scan(event) {
    event.preventDefault(); setError(''); setInvalid(false); setResult(null); setBusy(true);
    const submittedUrl = url.trim(); setUrl(submittedUrl);
    try {
      const response = await fetch(`${base}/scan`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:submittedUrl}), signal:AbortSignal.timeout(30000)});
      let data;
      try {data = await response.json();}
      catch {throw new Error('The scanner returned an unreadable response. Please try again.');}
      if (!response.ok) {setInvalid(response.status === 422); throw new Error(data.error?.message || 'The scan couldn’t finish. Please try again.');}
      setResult(data);
    } catch (e) {setError(e.name === 'TimeoutError' ? 'This scan took too long. Please try again.' : e.message === 'Failed to fetch' ? 'The scanner is disconnected. Check that the local API is running and try again.' : e.message);}
    finally {setBusy(false);}
  }
  const fixture = health?.mode === 'fixture';
  const reportUrl = health?.model_profile === 'release_cascade' ? releaseReportUrl : health?.cascade_status === 'available' ? neuralReportUrl : evaluationReportUrl;
  return <div className="shell">
    <a className="skip-link" href="#scanner-title">Skip to scanner</a>
    <header><a className="brand" href="/" aria-label="PhishX home"><Icon name="shield" width="29" height="32"/>PhishX</a><div className="header-links"><a href="#how-it-works">How it works</a><span className="prototype">Local prototype</span></div></header>
    <main>
      <div className="intro"><h1>Check a link<br/>before you click.</h1><p>Get a model-based risk score and understand the signals behind it.</p></div>
      <div className="workspace">
        <section className="scanner" aria-labelledby="scanner-title">
          <div className="section-title"><h2 id="scanner-title" tabIndex={-1}>Check a URL</h2><span role="status" className={`status ${health?.ready ? 'online' : ''}`}><span className="status-dot" aria-hidden="true"/>{health?.ready ? fixture ? 'Sample mode' : 'Ready to scan' : healthError || health ? 'Not connected' : 'Connecting…'}</span></div>
          {healthError && <div className="notice" role="status">{healthError} <button type="button" onClick={checkHealth}>Retry connection</button></div>}
          {fixture && <div className="notice">Sample mode: only the four examples below are supported. Their scores are illustrative, not measured predictions.</div>}
          {health?.mode === 'model' && !health.ready && <div className="notice">The model isn’t ready yet. Check the local API setup, then retry. <button type="button" onClick={checkHealth}>Retry connection</button></div>}
          <form onSubmit={scan} aria-busy={busy}>
            <label htmlFor="url">Paste the link you want to check</label>
            <div className="input-wrap"><Icon name="link"/><input ref={inputRef} id="url" type="text" inputMode="url" autoComplete="off" autoCapitalize="none" spellCheck="false" placeholder="https://example.com/" maxLength={2048} required value={url} onChange={e => changeUrl(e.target.value)} aria-describedby={error ? 'url-hint scan-error' : 'url-hint'} aria-invalid={invalid} disabled={busy}/>{url && <button type="button" className="clear-button" disabled={busy} onClick={() => {changeUrl('');inputRef.current?.focus();}} aria-label="Clear URL">Clear</button>}</div>
            <p id="url-hint" className="hint">Include <code>https://</code> or <code>http://</code>. Up to 2,048 characters.</p>
            <button className="primary" type="submit" disabled={busy || !url.trim()}>{busy ? 'Checking your link…' : 'Analyze URL'}<Icon name="arrow"/></button>
            {busy && <p className="feedback" role="status">Analyzing URL text and preparing the model explanation…</p>}
            {error && <p id="scan-error" className="error" role="alert">{error}</p>}
          </form>
          <div className="examples"><p>{fixture ? 'Choose a sample' : 'Or start with an example'}</p><div className="example-buttons">{(fixture ? fixtureExamples : modelExamples).map(([label,value]) => <button type="button" key={label} disabled={busy} onClick={() => {changeUrl(value);inputRef.current?.focus();}}>{label}</button>)}</div>{!fixture && <p className="example-note">Lookalike and subdomain examples are synthetic URL patterns, not verified phishing pages.</p>}</div>
          <p className="scanner-footnote">{fixture ? 'Sample responses only.' : 'The model analyzes the link, not the page’s content.'} Network checks are a separate, optional step.</p>
        </section>
        <aside className="scope" id="how-it-works"><h2>How it works</h2><ol className="guide"><li><strong>Paste a full link</strong><p>Use the complete website address, including its protocol.</p></li><li><strong>Review the model score</strong><p>Higher scores mean more model-detected phishing risk.</p></li><li><strong>Explore when you need to</strong><p>Open the explanation or request live domain checks after a scan.</p></li></ol><p className="safety-note"><Icon name="shield"/>A low score doesn’t guarantee safety. The model can make mistakes.</p>
          <details className="model-about"><summary>About this model</summary><dl className="details"><div><dt>Detection path</dt><dd>{health?.model_profile === 'release_cascade' ? 'RF + Char-CNN' : health?.cascade_status === 'available' ? 'Research cascade' : health?.ready ? 'Classical' : 'Unavailable'}</dd></div><div><dt>Live checks</dt><dd>{health?.live_signals_enabled ? 'Optional' : 'Disabled'}</dd></div></dl>{health?.model_notice && <p>{health.model_notice}</p>}<p>Scores are uncalibrated unless the result explicitly states otherwise.</p><a href={reportUrl} target="_blank" rel="noreferrer">Read the evaluation and limitations</a></details>
        </aside>
      </div>
      {result ? <ScanResult result={result} health={health} resultRef={resultRef}/> : <section className={`empty ${busy ? 'is-loading' : ''}`} aria-label={busy ? 'Analysis in progress' : 'No scan yet'}><Icon name="link"/><div><h2>{busy ? 'Checking your link…' : 'Ready when you are.'}</h2><p>{busy ? 'Your score and explanation will appear here.' : 'Paste a URL above, or choose an example to see how it works.'}</p></div></section>}
    </main>
    <footer><span>PhishX · Research prototype</span><a href={reportUrl} target="_blank" rel="noreferrer">Evaluation & limitations</a></footer>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
