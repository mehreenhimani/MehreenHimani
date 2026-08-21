# =====================================================================================
# Multi-stage build.
#
# Stage 1 compiles wheels with a toolchain; stage 2 ships a runtime that has no
# compiler, no package manager cache and no shell tooling an attacker would want. The
# result is a smaller image and a much smaller CVE surface — most "critical" findings
# in a naive Python image come from build dependencies that never needed to ship.
# =====================================================================================
FROM python:3.11-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential=12.9 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# -------------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

# Non-root by default. Container Apps does not force it, so the image has to.
RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

COPY --chown=app:app app ./app
COPY --chown=app:app static ./static

USER app
EXPOSE 8080

# Matches the Container App readiness probe, so `docker run` and Azure agree on what
# "healthy" means.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/readyz').status==200 else 1)"

CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
