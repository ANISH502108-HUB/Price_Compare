# Frontend Setup

## Install

```bash
npm install
```

## Run

```bash
npm run dev
```

The app runs on `http://localhost:3000`.

## Backend Proxy

Frontend API route `/api/search` proxies SSE requests to the backend.

Set `BACKEND_BASE_URL` if your backend is not on `http://127.0.0.1:8000`.

Example:

```bash
set BACKEND_BASE_URL=http://127.0.0.1:8000
```
