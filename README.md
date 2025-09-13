base project

```bash
$WORKSPACE/
├── app/ # FastAPI
│   ├── main.py
│   ├── __init__.py
│   └── ...
├── tests/ # pytest tests
│   ├── test_api.py
│   ├── test_models.py
│   └── ...
├── requirements.txt
├── Jenkinsfile
├── .venv/ # venv used for local dev.
├── .docker_venv/ # venv used for docker container
└── 
```

build image (from workdir root)
```bash
docker build -t fastapi-runtime:py312-slim -f environments/Dockerfile .
```