pipeline {
  agent { node { label 'docker-agent-fastapi' } }

  options {
    timestamps()
    timeout(time: 20, unit: 'MINUTES')
  }

  environment {
    PORT        = '9000'
    APP_MODULE  = 'app.main:app' // ASGI app path
    PIP_CACHE_DIR = "${WORKSPACE}/.pip-cache"
    PYTHONPATH  = "${WORKSPACE}"
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Deps') {
      steps {
        sh '''
          set -e
          mkdir -p "$PIP_CACHE_DIR"
          if [ -f requirements.txt ]; then
            echo "[deps] Installing requirements.txt..."
            pip3 install --no-cache-dir --cache-dir "$PIP_CACHE_DIR" -r requirements.txt
          else
            echo "[deps] No requirements.txt found; skipping."
          fi
        '''
      }
    }

    stage('Start FastAPI') {
      steps {
        sh '''
          set -e
          # Launch in background
          run-fastapi "$APP_MODULE" &
          echo $! > fastapi.pid

          # Wait until HTTP ready on /health or /
          for i in $(seq 1 60); do
            if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1 || \
               curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
              echo "[health] FastAPI is up."
              exit 0
            fi
            sleep 0.5
          done
          echo "[health] FastAPI did not become ready in time."
          exit 1
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -e
          # Your tests can hit http://127.0.0.1:${PORT}
          if [ -d test ] || [ -d tests ]; then
            pytest -q
          else
            echo "[test] No tests directory; skipping."
          fi
        '''
      }
    }
  }

  post {
    always {
      sh '''
        if [ -f fastapi.pid ]; then
          kill "$(cat fastapi.pid)" 2>/dev/null || true
          rm -f fastapi.pid
        else
          pkill -f "uvicorn" 2>/dev/null || true
        fi
      '''
    }
  }
}
