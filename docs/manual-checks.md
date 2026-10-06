# Manual checks for the application

Use fixture mode first; real model acceptance is a separate pass after handoff.
Record actual observations in person3-test-template.csv. Do not replace expected
results with fabricated actual results or label synthetic URLs as real phishing.

1. Start API and UI from README on a fresh checkout. Verify health mode/version.
2. Run all four example buttons; verify sample notice, score and band, brand,
   unavailable live signals, empty SHAP reasons and classical model path.
3. Enter a blank URL, unsupported scheme, whitespace and an unknown fixture URL.
   Confirm useful errors and recovery with a subsequent valid sample.
4. Stop the API. Refresh and retry connection; attempt a scan and verify an error.
5. Use keyboard only; check input label, visible focus, disabled loading controls
   and announced error/result. Repeat on narrow/mobile viewport without overflow.
6. Run model mode without PHISHX_PROVIDER; verify health not_ready and scan 503.
7. After Person 1 handoff: scan agreed labeled fixture, compare true probability
   and SHAP output to standalone inference. Record defects and real latency.

Person 3 fixture target from plan: 6 benign, 6 labeled phishing, 4 synthetic
homoglyph and 4 malformed. Person 1 supplies sources and validates labels.
Template rows intentionally contain no unverified URL labels or actual results.
Screenshots and one-page guide should come from the working integrated model demo.
