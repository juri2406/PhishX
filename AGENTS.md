# PhishX ownership and truth

Person 1 owns ml/, datasets, shared URL parser/features, skeleton matching and evaluation.
Person 2 owns backend/, frontend/ and application integration.
Person 3 supplies independent test fixtures and documentation after handoff.
Do not rewrite the training parser in the backend. Do not manufacture predictions,
SHAP reasons, evaluation metrics, screenshot evidence or model latency. Keep
fixture mode explicit, opt-in and separate from measured outputs. Do not claim
60% completion until the plan's acceptance evidence exists. Keep secrets,
raw datasets and model binaries out of Git. Changes to the proposed contract
must update README and docs/person1-handoff.md together.

Checks: .venv/Scripts/python.exe -m pytest backend/tests -q; frontend pnpm build.
