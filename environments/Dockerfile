FROM jenkins/agent:latest-alpine

USER root

# System deps
RUN apk add --no-cache \
      python3 py3-pip \
      curl bash git \
  && python3 -m venv /opt/venv \
  && chown -R jenkins:jenkins /opt/venv

# Ensure venv is always used
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and basics inside venv
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
         fastapi "uvicorn[standard]" pytest httpx

# Helper script
COPY run-fastapi.sh /usr/local/bin/run-fastapi
RUN chmod +x /usr/local/bin/run-fastapi

ENV APP_MODULE="app.main:app" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 9000
HEALTHCHECK --interval=30s --timeout=3s --retries=5 CMD curl -fsS http://127.0.0.1:9000/ || exit 1

USER jenkins
