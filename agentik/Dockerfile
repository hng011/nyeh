FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential graphviz-dev graphviz pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# uv may download the pinned Python; keep it outside /root so USER 1000 can run it.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Fail the build here, not minutes later as a Cloud Run startup timeout.
RUN uvicorn --version

# SQLite chat history; k8s mounts a persistent volume here.
ENV DATA_DIR=/data
RUN mkdir -p /data && chown 1000:1000 /data

# k8s chart enforces runAsNonRoot.
USER 1000:1000
ENV HOME=/tmp

# ponytail: Cloud Run injects $PORT, default 8080 for local `docker run`.
CMD uvicorn src.main:api --host 0.0.0.0 --port ${PORT:-8080}
