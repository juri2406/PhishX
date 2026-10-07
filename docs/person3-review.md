# Person 3 fixture and final review - 7 October 2026

The requested Person 3 deliverables are supplied: a separate 20-case fixture,
recorded browser/HTTP observations, a concise bug list, six actual screenshots
and a visually checked one-page PDF guide. Codex performed this review at the
user's request. No human teammate attendance, meeting or sign-off is asserted.

## Fixture independence and labels

Selection was fixed before model predictions. The six benign and six phishing
URL domain skeletons have zero overlap with every recorded processed set and
both observed UCI samples. Phishing examples were hash-sampled from unused
PhishTank groups; no selection or replacement used prediction outcomes. The
frozen run06 model was not retrained after review. This is independence from
training/evaluation examples, not a separate human reviewer or new data provider.

The six benign candidates are official publisher pages: [Svelte](https://svelte.dev/docs/svelte/overview),
[TypeScript](https://www.typescriptlang.org/docs/), [SolidJS](https://www.solidjs.com/),
[Tauri](https://v2.tauri.app/start/), [Zig](https://ziglang.org/learn/) and
[Nim](https://nim-lang.org/documentation.html). HTTP/title/hash checks are in
`evidence/person3/source-review.json`. Solid's raw HTML did not yield an
inspectable title; the live browser title and the [official repository's
website link](https://github.com/solidjs/solid) establish the publisher instead.
Official ownership is a candidate label basis, not certification against compromise.

PhishTank reports `verified=yes` and `online=yes` in the October snapshot.
Verification dates range from March 2024 to July 2026; pages were never visited.
These are source labels, not current independent live-page confirmation. Four
Unicode lookalikes use `.example` and remain explicitly synthetic. Four invalid
strings exercise scheme, host, encoding and whitespace errors.

Raw phishing URLs and the full 20-string CSV remain outside Git in
`artifacts/handoff/PhishX_person3_review_v6.zip`. The committed CSV/JSON summaries
use case IDs and URL hashes. They preserve provenance, labels and actual results.
The archive is a local review handoff, not a public dataset release.

## Recorded outcome

All 20 application cases passed: 16 real model-mode results matched standalone
probability, normalized host and SHAP items, and four invalid inputs showed
useful validation errors. Class 1, probability-scale SHAP and additivity were
checked through the existing adapter. All scans went through the real browser
and Vite proxy. No fixture provider or invented prediction was used.

| Group | Cases | Application outcome | Detection observations |
|---|---:|---|---|
| Benign publisher candidates | 6 | All matched real API/model | Two false positives |
| Source-labeled phishing | 6 | All matched real API/model | One missed source label |
| Synthetic homoglyph strings | 4 | All parsed; real scores/explanations | Not a real phishing accuracy sample |
| Malformed inputs | 4 | All rejected with visible errors and HTTP 422 | Not detection cases |

Do not report 20/20 application passes as 100% detection accuracy. Twelve source-
labeled cases are too few and too selective for a benchmark. The two benign
false positives scored 62 (TypeScript) and 84 (Tauri); source phishing case 1
scored 6. Full actual observations are in `evidence/person3/fixture-results.json`
and `person3-fixture-results.csv`, with private URL details in the archive.

## Bug list and disposition

- **MODEL-01, open research issue:** TypeScript and Tauri false positives.
  Person 1 owns future data/model improvements; no whitelisting was added.
- **MODEL-02, open research issue:** source phishing case 1 missed at score 6.
  Source age and labeling limits remain visible. A low score cannot guarantee safety.
- **MODEL-03, retained known issue:** the previously observed GitHub repository
  control remains a false positive at 55 in run06. It was not relabeled benign
  by the application or quietly removed from the earlier report.
- **Application blockers:** none observed in this focused pass. Browser results,
  malformed inputs, keyboard/focus, mobile layout, loading and outage recovery
  matched the declared prototype behavior. Returned console error/warning logs
  were empty in the final review; this is not comprehensive browser certification.

These model-quality findings block a production-quality claim, not the plan's
experimental classical prototype. No target accuracy or zero-error requirement
was specified in the plan. This review reports defects; it does not modify
Person 1's frozen model.

## Manual pass and screenshots

Keyboard Enter submitted and focused the result. Tab focus on submit used a
solid 3 px outline. Empty submit stayed disabled. Input, submit and all example
controls were disabled during loading, observed using a temporary 1.5-second
middleware delay around the real provider. That wrapper was not shipped and
was removed before latency measurement. Stopping the real API showed a health
notice and scan error; restarting it and selecting Retry connection recovered.

Measured viewport widths were 390 px and 320 px, with no horizontal overflow;
example targets were 44 px tall. The first viewport attempt affected another
selected tab; those captures were replaced after measuring actual dimensions
on the dedicated mobile tab. No claim is based on a requested-but-unapplied size.

Six original captures:

- [Desktop empty](evidence/person3/desktop-empty.jpg)
- [Benign model result](evidence/person3/desktop-benign.jpg)
- [Synthetic Unicode result](evidence/person3/desktop-synthetic.jpg)
- [Mobile synthetic result, 390 px](evidence/person3/mobile-synthetic.jpg)
- [Mobile validation error, 320 px](evidence/person3/mobile-validation.jpg)
- [Actual API offline](evidence/person3/backend-offline.jpg)

The benign desktop image captures the scanner and start of the result at the
top of the page. Other full-page results include all observed features. No raw
phishing URL appears in these committed screenshots.

## Guide and local acceptance

[One-page scanner guide](person3-user-guide.pdf) covers setup, trusted model
handoff, scanning, score interpretation and recovery. It was rendered and
visually reviewed as one page. Person 2's revised-model acceptance is in
[person23-acceptance.md](person23-acceptance.md); the final evidence index is
[milestone-acceptance.md](milestone-acceptance.md). The role deliverables are
complete for the local classical milestone. Human teammate review is not
manufactured; future cascade/live checks/deployment remain outside this scope.
