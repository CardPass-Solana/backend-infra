FROM alpine:latest

WORKDIR /home
RUN apk add --no-cache git python3 py3-pip

RUN git clone https://github.com/CardPass-Solana/backend-infra.git
WORKDIR /home/backend-infra

RUN python3 -m venv .venv \
 && /home/backend-infra/.venv/bin/pip install --no-cache-dir -r requirements.txt \
 && /home/backend-infra/.venv/bin/pip install --no-cache-dir "fastapi[standard]"

# Make venv binaries available to CMD
ENV PATH="/home/backend-infra/.venv/bin:${PATH}"

EXPOSE 8000
CMD ["fastapi", "dev", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["/home/backend-infra/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
