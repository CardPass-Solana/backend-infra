pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    IMAGE           = 'fastapi-runtime:py312-slim'
    CONTAINER_NAME  = 'fastapi-sidecar'
    APP_PORT        = '9000'
    HOST_PORT       = '9000'
    APP_DIR_IN_CONT = '/app'
    APP_IMPORT      = 'main:app'  // change if FastAPI app has a different module:var
  }

  triggers {
    // Poll SCM every 2 minutes
    pollSCM('H/2 * * * *')
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Start or Reuse Sidecar') {
      steps {
        sh '''
          set -euo pipefail

          # Pull image if not present (THROWS ERROR FOR NOW, LOCAL BUILD ONLY)
          if ! docker image inspect "$IMAGE" > /dev/null 2>&1; then
            # echo "Pulling image $IMAGE ..."
            # docker pull "$IMAGE" || true
            echo "Image $IMAGE not found locally"
            exit 1
          fi

          # Create a user-defined network once
          if ! docker network inspect fastapi_net > /dev/null 2>&1; then
            docker network create fastapi_net
          fi

          # If container exists but is stopped, start it. If running, reuse it.
          if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
            if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" = "true" ]; then
              echo "Container $CONTAINER_NAME already running. Reusing."
              # ensure env is correct; optional restart to pick updated env
              # docker restart "$CONTAINER_NAME"
            else
              echo "Starting existing container $CONTAINER_NAME ..."
              docker start "$CONTAINER_NAME"
            fi
          else
            echo "Launching new container $CONTAINER_NAME ..."
            docker run -d --name "$CONTAINER_NAME" \
              --network fastapi_net \
              -p "$HOST_PORT:$APP_PORT" \
              -e APP_IMPORT="$APP_IMPORT" \
              -e PORT="$APP_PORT" \
              -v "$PWD":"$APP_DIR_IN_CONT":rw \
              "$IMAGE"
          fi

          echo "Waiting for service to respond ..."
          for i in $(seq 1 40); do
            if curl -fsS "http://127.0.0.1:$HOST_PORT/health" >/dev/null 2>&1 || \
               curl -fsS "http://127.0.0.1:$HOST_PORT/" >/dev/null 2>&1; then
              echo "Service is up."
              exit 0
            fi
            sleep 1
          done

          echo "Service did not become healthy in time."
          docker logs --tail=200 "$CONTAINER_NAME" || true
          exit 1
        '''
      }
    }

    stage('Unit/Integration Tests') {
      steps {
        // Example: run pytest inside the container against mounted source
        // sh '''
        //   set -euo pipefail
        //   # If you keep tests in ./tests, this runs inside the same runtime
        //   # Adjust command if you use tox or no pytest.
        //   docker exec "$CONTAINER_NAME" /venv/bin/python -m pytest -q || {
        //     echo "Tests failed. Showing last logs:"
        //     docker logs --tail=200 "$CONTAINER_NAME" || true
        //     exit 1
        //   }
        // '''
        sh 'echo "No tests defined. Skipping."'
      }
    }

    stage('Smoke Check') {
      steps {
        sh '''
          set -euo pipefail
          curl -fsS "http://127.0.0.1:$HOST_PORT/" >/dev/null || {
            echo "Smoke check failed."
            exit 1
          }
          echo "Smoke check passed."
        '''
      }
    }
  }

  post {
    always {
      script {
        // Keep container running for manual testing
        echo "$CONTAINER_NAME running on port ${HOST_PORT}"
        echo "To rebuild deps, update requirements.txt and push; container will auto-install on restart."
      }
    }
    failure {
      sh '''
        echo "Build failed. Container logs tail:"
        docker logs --tail=200 "$CONTAINER_NAME" || true
      '''
    }
  }
}
