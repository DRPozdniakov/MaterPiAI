# MasterPi AI

UCL Hackathon project.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Test

```bash
pytest tests/ -v
```
