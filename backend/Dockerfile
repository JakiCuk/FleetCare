# FleetCare backend image (FastAPI + Celery share the same image).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps for argon2-cffi / asyncpg / matrix-nio (libolm) wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libolm-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Build version (yyyymmddhhmm), injected by CI; "dev" for local builds.
ARG BUILD_VERSION=dev
ENV BUILD_VERSION=$BUILD_VERSION

COPY . .

# Normalize line endings (a CRLF checkout on Windows would break the shebang)
# and make the entrypoint executable.
RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
