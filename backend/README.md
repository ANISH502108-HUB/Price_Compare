# Backend Setup

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## API

- `GET /health`
- `GET /search?item=milk&pincode=411001` (SSE stream)
