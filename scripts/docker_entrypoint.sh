#!/bin/sh
set -eu

RUNTIME_ROOT="/app/runtime-data"
SEED_ROOT="/app/seed-data"

mkdir -p "${RUNTIME_ROOT}/index" "${RUNTIME_ROOT}/processed"

if [ ! -f "${RUNTIME_ROOT}/processed/events.parquet" ] && [ -f "${SEED_ROOT}/processed/events.parquet" ]; then
  cp "${SEED_ROOT}/processed/events.parquet" "${RUNTIME_ROOT}/processed/events.parquet"
fi

if [ ! -f "${RUNTIME_ROOT}/index/index_manifest.json" ] && [ -f "${SEED_ROOT}/index/index_manifest.json" ]; then
  cp "${SEED_ROOT}/index/index_manifest.json" "${RUNTIME_ROOT}/index/index_manifest.json"
fi

if [ ! -f "${RUNTIME_ROOT}/index/indexed_documents.parquet" ] && [ -f "${SEED_ROOT}/index/indexed_documents.parquet" ]; then
  cp "${SEED_ROOT}/index/indexed_documents.parquet" "${RUNTIME_ROOT}/index/indexed_documents.parquet"
fi

if [ ! -d "${RUNTIME_ROOT}/index/faiss" ] && [ -d "${SEED_ROOT}/index/faiss" ]; then
  mkdir -p "${RUNTIME_ROOT}/index/faiss"
  cp -R "${SEED_ROOT}/index/faiss/." "${RUNTIME_ROOT}/index/faiss/"
fi

export INDEX_OUTPUT_DIR="${INDEX_OUTPUT_DIR:-${RUNTIME_ROOT}/index/faiss}"
export INDEX_INPUT_PATH="${INDEX_INPUT_PATH:-${RUNTIME_ROOT}/processed/events.parquet}"

exec python /app/scripts/run_api.py
