# Human acceptance record

Status: **Pending user execution and report**. The user volunteered to perform
these checks. Codex has not signed on the user's behalf. Automated test results
and model-quality results are separate evidence.

Open http://127.0.0.1:8080 on this Mac. To start from the repository root, run
`bash scripts/demo.sh`. Keep the displayed model version in your report.
Never open synthetic or historical phishing target URLs in another browser tab;
submit them as text to PhishX only.

| ID | Action | What to verify | Human outcome |
| --- | --- | --- | --- |
| H1 | Open the demo and scan `https://example.com/` | API ready; actual score, model version and explanation visible. A low score is not a safety guarantee. Record the score/version. | Pending |
| H2 | Choose Synthetic lookalike and analyze | The result shows the normalized Punycode host and observed Unicode/brand signals. Record its score; do not substitute a desired score. | Pending |
| H3 | Submit `javascript:alert(1)` | An understandable validation error appears; no successful result is presented for this input. | Pending |
| H4 | Scan example.com, then choose Run live checks | DNS/TLS/redirect/domain-age observations appear with honest available/unavailable statuses and messages; model score stays unchanged. | Pending |
| H5 | Scan `http://127.0.0.1/`, then request live checks | The live target is blocked. Offline URL-text analysis may still return a score. | Pending |
| H6 | Analyze using Enter, then press Tab after results | Focus moves to the result, then to its Run live checks button. Narrow the window to phone width and check for clipped content or horizontal scrolling. | Pending |
| H7 | Run `bash scripts/demo.sh stop`, then `bash scripts/demo.sh` | Containers restart and the demo becomes ready again on localhost:8080. | Pending |
| H8 | Read the score notice and completion report | You understand scores are uncalibrated and model/site safety are different; review the recorded model mistakes and sample limitations. | Pending |

Reply with the model version, H1-H8 pass/fail, actual scores for H1/H2, and any
problem you observed. Report partial results honestly; untested cases stay pending.
No production certification, independent audit or human identity verification is
implied by this classroom demo acceptance.
