# DemoMB

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install pip-tools
pip-compile requirements.in -o requirements.txt
pip-compile requirements-dev.in -o requirements-dev.txt
pip-sync requirements.txt requirements-dev.txt  # si tienes pip-tools (pip-sync)
pre-commit install
```

## Run (app/script)
```bash
python -m demomb
```

## Test
```bash
pytest
```

## Lint/Format
```bash
pre-commit run -a
# o:
ruff check . --fix
ruff format .
```
