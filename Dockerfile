FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    INDEX_OUTPUT_DIR=/app/runtime-data/index/faiss \
    INDEX_INPUT_PATH=/app/runtime-data/processed/events.parquet

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple \
        torch==2.13.0+cpu \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY scripts /app/scripts
COPY README.md /app/README.md
COPY seed-data/index /app/seed-data/index
COPY seed-data/processed /app/seed-data/processed

RUN chmod +x /app/scripts/docker_entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/scripts/docker_entrypoint.sh"]
