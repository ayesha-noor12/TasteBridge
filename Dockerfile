# One image: Node (qloo CLI) + Python (FastAPI) + the built frontend.

# ---- Build the frontend ----
FROM node:22.23.1-bookworm-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build -- --outDir /web/dist

# ---- Runtime ----
FROM node:22.23.1-bookworm-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    QLOO_MODE=mock LLM_MODE=off CACHE_DIR=/app/cache PORT=8000 HOME=/app
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g @qloo/qloo-harness@0.1.26 \
 && qloo --version
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app
COPY backend/data backend/data
COPY backend/tests/fixtures backend/tests/fixtures
COPY backend/scripts backend/scripts
COPY --from=web /web/dist backend/static
RUN useradd --create-home --uid 10001 app && mkdir -p /app/cache && chown -R app /app
USER app
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK CMD python3 -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health')" || exit 1
CMD ["sh", "-c", "/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
