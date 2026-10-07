# Receiving the revised experimental model

The current local review artifact is shared separately from Git in
`artifacts/handoff/PhishX_model_handoff_v6.zip`. Pull `gauri`, then extract the
archive into the repository root. The model lands at
`artifacts/revised-run06/classical.joblib`. Install the packages in
[the setup guide](person1-vscode.md), verify the checksum, and run VS Code task
**PhishX model backend**. On Windows `scripts/start-model.ps1` verifies run06 by
default; `-ModelRun uci-run03` selects the previous artifact explicitly.

Version `rf-v6-d5923fe7d93e-20261007`; SHA256
`a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed`.
The 24-feature extended profile requires the matching extended extractor hash
in addition to the base/resource hashes. No compatibility checks are bypassed.
The ZIP contains model weights, aggregate evaluation, model metadata/checksum,
requirements and guides; it contains no raw datasets. Load trusted files only.

See [run06 evaluation](evaluation-run06.md). The model is experimental, raw
probabilities are uncalibrated, and the GitHub repository path remains a known
false positive. The 20-row API check verifies integration, not a new accuracy
evaluation. Person 2 browser acceptance from run03 remains historical evidence
for that version; it is not reattributed to the revised model.

The ZIP/model remain ignored, so a Git clone alone cannot run this artifact.
The local supplemental Person 3 source package is
`artifacts/handoff/person3-review-v6.csv`; it contains source-labeled examples
and explicit synthetic/malformed cases. It is a developer handoff, not an
independent Person 3 review. Person 3 should independently check labels,
select their fixture, record results and review the demo.

## Previous run03 handoff (historical)

`artifacts/handoff/PhishX_model_handoff.zip` contains the earlier model at
`artifacts/uci-run03/classical.joblib`, version `rf-v2-1774537c789e-seed42`, SHA256
`2b59557ed0a23220bd69e0f2775ad934d20fa1587ff71fe2decb750fb2ff8ac7`.
It uses 18 features and remains supported for reproducing historical evidence.
To run it, use `scripts/start-model.ps1 -ModelRun uci-run03` or explicitly set
PHISHX_MODEL_PATH. Current default VS Code launch configs select run06.
See [run03 evaluation](evaluation-run03.md) for its same-source historical
results. No run03 checks are reattributed to run06.
