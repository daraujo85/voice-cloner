FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 UV_PROJECT_ENVIRONMENT=/opt/venv
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip ffmpeg sox curl && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --no-cache-dir uv==0.8.15
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen
COPY . .
RUN mkdir -p /app/output
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s CMD curl -fsS http://localhost:8787/health || exit 1

# Keep container logs bounded; Docker daemon may override these defaults.
CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8787"]
