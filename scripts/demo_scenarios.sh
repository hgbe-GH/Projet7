#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-90}"

wait_for_api() {
  local elapsed=0
  while ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; do
    if (( elapsed >= TIMEOUT_SECONDS )); then
      echo "API not ready after ${TIMEOUT_SECONDS}s: ${BASE_URL}/health" >&2
      return 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
}

ask() {
  local question="$1"
  echo
  echo "Question: ${question}"
  local response
  response="$(curl -fsS -X POST "${BASE_URL}/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"${question}\"}")"
  RESPONSE_JSON="${response}" python - <<'PY'
import json
import os

payload = json.loads(os.environ["RESPONSE_JSON"])
print("Reponse:")
print(payload["answer"])
print("Sources:")
for source in payload.get("sources", [])[:3]:
    title = source.get("title") or "Sans titre"
    city = source.get("city") or "ville inconnue"
    url = source.get("canonical_url") or "url absente"
    print(f"- {title} | {city} | {url}")
PY
}

wait_for_api

ask "Parle-moi de Concert Fishers a Paris"
ask "Parle-moi de SALON DE LA PHOTO a Paris"
ask "Je cherche une sortie en famille a Paris avec une visite theatricalisee"
