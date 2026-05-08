# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: dependency builder
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

# Only copy requirements so this layer is cached unless deps change
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Playwright browser installer
# Separate stage keeps browser cache in its own layer
# ─────────────────────────────────────────────────────────────────────────────
FROM mcr.microsoft.com/playwright/python:v1.50.0-noble AS playwright-base

# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: production runtime
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# --- System libraries required by Chromium -----------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libwayland-client0 \
    fonts-liberation \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Non-root user -----------------------------------------------------------
RUN groupadd -r tracker && useradd -r -g tracker -m tracker

# --- Python packages from builder --------------------------------------------
COPY --from=builder /install /usr/local

# --- Playwright + Chromium from official image -------------------------------
COPY --from=playwright-base /ms-playwright /ms-playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# --- App source --------------------------------------------------------------
WORKDIR /app

COPY --chown=tracker:tracker \
    api.py \
    calibrate.py \
    database.py \
    tracker.py \
    price_utils.py \
    ./

# --- Data volume (SQLite lives here) -----------------------------------------
RUN mkdir -p /app/data && chown tracker:tracker /app/data
VOLUME ["/app/data"]

# --- Runtime env defaults ----------------------------------------------------
ENV DB_PATH=/app/data/price_tracker.db \
    PORT=8001 \
    HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER tracker

EXPOSE 8001

# --- Health check ------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=15s --start-period=15s --retries=3 \
    CMD python -c \
        "import urllib.request,os; urllib.request.urlopen('http://localhost:'+os.getenv('PORT','8001')+'/health',timeout=10)"

# --- Entrypoint --------------------------------------------------------------
CMD ["sh", "-c", "uvicorn api:app --host $HOST --port $PORT --workers 1 --loop uvloop --access-log --log-level info"]
