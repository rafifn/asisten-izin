# Build from the repo root (the image also carries db/ migrations and data/):
#   docker build -f api/Dockerfile -t asisten-izin-api .
ARG PYTHON_IMAGE=python:3.12-slim

FROM ${PYTHON_IMAGE} AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /build
COPY api/pyproject.toml api/uv.lock ./
RUN uv venv /opt/venv
# CPU-only PyTorch: install torch from the PyTorch CPU index first, then everything else
# from the lock file without torch or the CUDA packages it would pull from PyPI.
RUN set -eu; \
    TORCH_VERSION="$(awk '/^name = "torch"$/ {getline; gsub(/[^0-9.]/, "", $0); print; exit}' uv.lock)"; \
    uv export --frozen --no-dev --no-hashes --no-emit-project -o requirements.txt; \
    grep -v -E '^(torch|triton|nvidia-[a-z0-9-]+|cuda-[a-z0-9-]+)==' requirements.txt > requirements-cpu.txt; \
    VIRTUAL_ENV=/opt/venv uv pip install --index-url https://download.pytorch.org/whl/cpu "torch==${TORCH_VERSION}"; \
    VIRTUAL_ENV=/opt/venv uv pip install -r requirements-cpu.txt
# Model weights are baked into the image so the container starts without a download.
ENV HF_HOME=/opt/hf
RUN /opt/venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
# The hub cache keeps the weights twice (shared blob store plus snapshot symlinks): keep one
# real copy, then check the model still loads offline.
RUN set -eu; \
    cd /opt/hf/hub/models--BAAI--bge-m3/snapshots/*/; \
    for f in $(find . -type l); do cp --remove-destination "$(readlink -f "$f")" "$f"; done; \
    rm -rf /opt/hf/hub/blobs /opt/hf/hub/models--BAAI--bge-m3/blobs /opt/hf/xet; \
    HF_HUB_OFFLINE=1 /opt/venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

FROM ${PYTHON_IMAGE}
RUN useradd --system --create-home --uid 1000 app
ENV PATH=/opt/venv/bin:$PATH \
    HF_HOME=/opt/hf \
    HF_HUB_OFFLINE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MIGRATIONS_DIR=/app/db/migrations
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/hf /opt/hf
WORKDIR /app
# Layout: /app/app (package), /app/db/migrations (MIGRATIONS_DIR above), /app/data (pass it to
# the loader: `python -m app.data.loader /app/data`).
COPY api/app ./app
COPY db ./db
COPY data ./data
COPY api/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && chown -R app:app /app
USER app
EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
