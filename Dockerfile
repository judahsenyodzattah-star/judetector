# JUDEtector inference API.
#
#   docker build -t judetector-api .
#   docker run --rm -p 8080:8080 judetector-api
#
# Weights are never baked into the image (they are git-ignored and may be large).
# Mount them and point the service at the file:
#
#   docker run -p 8080:8080 \
#     -v /path/to/models:/models:ro \
#     -e JUDETECTOR_MODEL_PATH=/models/best.pt \
#     judetector-api
#
# Without weights the service still starts and reports `degraded` from
# /v1/health. That is intentional: an honest unavailable state beats a crash.

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    JUDETECTOR_ENV=production \
    PORT=8080

WORKDIR /srv

COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY app ./app
COPY api ./api
COPY config ./config
COPY metrics ./metrics

# Run as a non-root user.
RUN useradd --create-home --uid 10001 judetector \
    && chown -R judetector:judetector /srv
USER judetector

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=6s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/v1/health', timeout=2).status == 200 else 1)"

CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
