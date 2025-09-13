# Base: Jenkins inbound agent (Alpine)
FROM jenkins/agent:latest-alpine

# Use root to install packages, then drop back to jenkins
USER root

# System deps and Python toolchain
# Keep it lean; add build-base only if you know you compile wheels often.
RUN apk add --no-cache \
      python3 py3-pip \
      curl bash git \
  && python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip3 install --no-cache-dir \
      fastapi "uvicorn[standard]" pytest httpx

# Helper to run FastAPI from the Jenkins workspace
COPY run-fastapi.sh /usr/local/bin/run-fastapi
RUN chmod +x /usr/local/bin/run-fastapi

# Defaults
ENV APP_MODULE="app.main:app" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# FastAPI port
EXPOSE 9000

# Basic healthcheck against the app root
HEALTHCHECK --interval=30s --timeout=3s --retries=5 CMD curl -fsS http://127.0.0.1:9000/ || exit 1

# Back to the non-root Jenkins user; entrypoint/cmd remain the agent's
USER jenkins
