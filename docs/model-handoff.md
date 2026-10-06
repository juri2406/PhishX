# Receiving the experimental model

The trained model is shared separately from Git. Ask Person 1 for
`PhishX_model_handoff.zip`, prepared locally at
`artifacts/handoff/PhishX_model_handoff.zip`.

1. Pull `codex/person1` from this repository.
2. Extract the archive into the repository root. The model must land at
   `artifacts/uci-run03/classical.joblib`.
3. Follow [the VS Code setup guide](person1-vscode.md) to create the environment
   and install the backend, ML dependencies, and repository package.
4. Verify the model SHA256 against the value below before loading it.
5. Open the repository folder in VS Code. Select **Terminal → Run Task →
   PhishX model backend**.

Model SHA256:
`2b59557ed0a23220bd69e0f2775ad934d20fa1587ff71fe2decb750fb2ff8ac7`.

Model version: `rf-v2-1774537c789e-seed42`. Compatible ML code is commit
`fc2b8bb` or descendants that preserve its extractor. Artifact loading checks
the feature schema, extractor hashes, and Unicode/brand resource hashes.
Do not bypass a mismatch; use compatible code or retrain.

The archive includes setup instructions, pinned ML dependencies, the evaluation
report, and a checksum file. It contains no raw dataset. Load only the trusted
Person 1 artifact: joblib files can execute Python objects during loading.

Handoff verification passed 46 tests and checked API predictions and SHAP
class, probability scale, and additivity on 20 real held-out URLs. This verifies
integration, not additional independent accuracy. See [the evaluation
report](evaluation-run03.md) for the 4,000-record historical-source results.
The model remains experimental, has uncalibrated probabilities, and produces
known false alarms on some legitimate navigation paths.

Model binaries and the ZIP remain ignored and are not available through a Git
clone. If the artifact is unavailable, use the reproduction guide to train it.
