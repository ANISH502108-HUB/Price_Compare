# Quick Deploy Runbook

This runbook deploys the project in one afternoon with a simple split architecture:

- frontend: Next.js on Vercel
- backend: FastAPI on a free Ubuntu VM
- communication: frontend `/api/search` proxy -> backend `/search` (SSE)

## Recommended Path (Default)

Use this as the default learning setup:

1. Deploy backend on VM with `uvicorn` + `systemd`
2. Put Caddy in front for HTTPS and reverse proxy
3. Deploy frontend on Vercel
4. Set `BACKEND_BASE_URL` in Vercel
5. Verify health and streaming end-to-end

## Simpler Fallback (If You Get Stuck)

Skip HTTPS and domain temporarily:

- run backend on `http://<VM_IP>:8000`
- set Vercel `BACKEND_BASE_URL` to that URL
- verify first, then add Caddy + domain later

## 1) Prerequisites

- GitHub repo connected to Vercel
- free Ubuntu VM with SSH access
- optional domain for backend HTTPS (recommended)

Assumed repo layout:

- `frontend/` Next.js app
- `backend/` FastAPI app

## 2) Backend Setup on Ubuntu VM

### Install dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git caddy
```

### Clone and install Python packages

```bash
git clone <repo-url> app
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Smoke test backend locally

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another SSH session:

```bash
curl -i http://127.0.0.1:8000/health
```

### Create systemd service

Create `/etc/systemd/system/grocery-backend.service`:

```ini
[Unit]
Description=Grocery FastAPI backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/app/backend
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/ubuntu/app/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now grocery-backend
sudo systemctl status grocery-backend
```

## 3) Add Caddy Reverse Proxy (Streaming Friendly)

If you have a domain, point `api.<your-domain>` A record to the VM IP.

Create `/etc/caddy/Caddyfile`:

```caddy
api.<your-domain> {
    reverse_proxy 127.0.0.1:8000 {
        flush_interval -1
    }
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy
```

Notes for streaming endpoints:

- keep `text/event-stream`
- disable buffering (`flush_interval -1`)
- keep long-lived connections alive

## 4) Frontend Deployment to Vercel

In Vercel project settings:

- Root Directory: `frontend`
- Framework Preset: Next.js
- Build Command: default
- Output Directory: default

Set environment variable:

- `BACKEND_BASE_URL=https://api.<your-domain>`

Fallback value (no domain yet):

- `BACKEND_BASE_URL=http://<VM_IP>:8000`

Deploy the frontend.

## 5) Frontend <-> Backend Communication

Current frontend implementation already proxies SSE through `frontend/app/api/search/route.ts` using:

- `BACKEND_BASE_URL`
- upstream endpoint `/search`
- request header `Accept: text/event-stream`

This means browser calls same-origin Vercel route `/api/search`, so CORS is usually not required.

If you later call backend directly from browser, add FastAPI CORS for only your Vercel origin.

## 6) Verification Checklist

### Backend health through public URL

```bash
curl -i https://api.<your-domain>/health
```

Expected: `200` and `{"status":"ok"}`.

### Backend streaming endpoint directly

```bash
curl -N -H "Accept: text/event-stream" "https://api.<your-domain>/search?item=milk&pincode=411001"
```

Expected: streamed SSE events over time.

### End-to-end streaming through Vercel

```bash
curl -N "https://<your-vercel-app>.vercel.app/api/search?item=milk&pincode=411001"
```

Expected: streamed SSE events from backend via frontend proxy.

### Browser verification

- open deployed frontend
- perform a search
- in DevTools Network, confirm `/api/search?...` stays open while events stream

## 7) Common Issues and Fast Fixes

- `502 Backend search stream unavailable` from frontend:
  - check Vercel `BACKEND_BASE_URL`
  - ensure VM security group/firewall allows inbound `80/443` (or `8000` for fallback)
- health works, stream stalls:
  - ensure proxy buffering is disabled (`flush_interval -1` in Caddy)
- HTTPS certificate not issued:
  - fix DNS A record to VM public IP, wait a few minutes, reload Caddy
- service restarts repeatedly:
  - check logs: `journalctl -u grocery-backend -n 100 --no-pager`
  - verify `WorkingDirectory` and `.venv` paths
- CORS errors (only if direct browser -> backend):
  - add FastAPI CORS middleware with exact Vercel origin

## 8) Afternoon Execution Order

1. Backend local smoke test on VM
2. systemd service setup
3. Caddy reverse proxy and HTTPS
4. Vercel deploy + env var
5. curl checks for health + SSE
6. browser end-to-end validation
