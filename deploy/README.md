# Container deployment candidate

This configuration has not yet been built here: Docker is not installed on the
current host. It is a local deployment candidate, not a verified hosted release.

1. Obtain the trusted v6 model handoff separately and verify its SHA-256:
   `a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed`.
   Place it at `artifacts/revised-run06/classical.joblib`. Never put it in Git or
   bake it into an image. The directory is mounted read-only.
2. On a Docker/Compose host, run from the repository root:

   ```bash
   docker compose build
   docker compose up -d
   docker compose ps
   curl --fail http://127.0.0.1:8080/api/health
   ```

3. Open http://127.0.0.1:8080 and perform a real scan. Check `ready: true`, model
   version, SHAP results and a malformed URL. Backend is not published directly.
4. Live checks default to off. To enable:

   ```bash
   PHISHX_LIVE_SIGNALS=1 docker compose up -d --force-recreate backend
   docker compose restart frontend
   ```

   Test example.com and a blocked private address through `/api/signals`.
   Verify timeouts and 429 behavior; never use a private target as success evidence.
5. Stop with `docker compose down`.

Before external publication, select a host, terminate HTTPS, restrict access for
an academic demo, apply network-level egress blocks for internal/metadata ranges,
and verify resource limits/rate limits on that platform. The web port binds only
to localhost intentionally. No external hosting credentials or destination have
been selected. The frozen model's dependencies are pinned in the existing verified
requirements files; the container recipe itself still needs a build verification.

If hosting frontend separately, set `VITE_API_BASE` at build time and
`PHISHX_ALLOWED_ORIGINS` as a comma-separated exact origin list on the API. The
included same-origin proxy requires neither setting.

The supplied backend image serves the established classical provider. The optional
neural research provider needs the separate `ml/requirements-neural.txt` and
private neural handoff; it is not enabled or installed by this deployment recipe.
