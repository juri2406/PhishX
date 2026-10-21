# Local Docker demo

Run from the repository root:

```bash
bash scripts/demo.sh
```

Open http://127.0.0.1:8080. Manage it with `bash scripts/demo.sh status`,
`bash scripts/demo.sh logs`, and `bash scripts/demo.sh stop`.
The script supports Docker Desktop or a dedicated Colima `phishx` VM on this Mac.
Docker and Compose must be installed. The first build downloads dependencies.
Only localhost port 8080 is published; backend port 8000 stays internal.

The default is the existing classical RF v6 provider with real TreeSHAP, not the
experimental cascade. Obtain its trusted private model handoff separately and put
it at `artifacts/revised-run06/classical.joblib`. Verify SHA-256:
`a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed`.
The model folder mounts read-only; weights and raw data are excluded from Git.

Live checks are enabled but run only after the user explicitly requests them.
To disable them start with `PHISHX_LIVE_SIGNALS=0 bash scripts/demo.sh`.
They do not change the model score. The image runs the API as a nonroot user,
with a read-only root filesystem and temporary `/tmp`. Nginx provides same-origin
API proxying, security headers, request-size and rate limits. These settings are
for the local academic demo; no public deployment or production acceptance is claimed.

See [completion status](../docs/project-completion.md) for failed research gates
and remaining model-quality work. Stop the dedicated VM to release its memory with
`colima stop phishx` after stopping the containers.
