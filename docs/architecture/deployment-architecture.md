# Deployment Architecture

## Overview

The system is deployed using separate frontend and backend environments.

---

## Deployment Diagram

User
↓
Frontend (Vercel)
↓
Backend API (Cloud VM)
↓
Scrapers

---

## Frontend Deployment

Hosted on Vercel.

Responsibilities:

- serve UI
- send API requests
- display results

---

## Backend Deployment

Hosted on a free cloud virtual machine.

Responsibilities:

- scraping
- product matching
- API responses

Possible platforms:

- Oracle Cloud free tier
- Fly.io free tier

---

## Benefits of Split Deployment

- frontend scaling independent of backend
- backend can run long scraping tasks
- avoids serverless execution limits
