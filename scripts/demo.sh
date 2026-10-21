#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -z "${DOCKER_HOST:-}" && -S "$HOME/.colima/phishx/docker.sock" ]]; then
  export DOCKER_HOST="unix://$HOME/.colima/phishx/docker.sock"
fi
if ! docker info >/dev/null 2>&1; then
  if command -v colima >/dev/null 2>&1; then
    colima start phishx --activate=false --cpus 2 --memory 3 --disk 20 --vm-type vz --ssh-config=false
    export DOCKER_HOST="unix://$HOME/.colima/phishx/docker.sock"
  else
    echo 'Start Docker Desktop, or install Colima and Docker first.' >&2
    exit 1
  fi
fi
if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  compose=(docker-compose)
else
  echo 'Install Docker Compose first.' >&2
  exit 1
fi
case "${1:-start}" in
  start)
    if [[ ! -f artifacts/release-v3/classical.joblib || ! -f artifacts/release-v3/charcnn.pt ]]; then
      echo 'Extract the trusted PhishX final model handoff into this repository first.' >&2
      exit 1
    fi
    "${compose[@]}" up -d --build --wait --wait-timeout 180
    echo 'PhishX is ready at http://127.0.0.1:8080'
    ;;
  stop) "${compose[@]}" down ;;
  status) "${compose[@]}" ps ;;
  logs) "${compose[@]}" logs --tail=80 ;;
  *) echo 'Usage: bash scripts/demo.sh [start|stop|status|logs]' >&2; exit 2 ;;
esac
