# Grocery Price Comparison App

A web application that compares grocery prices across quick-commerce platforms in real time.

Currently supported platforms:

- Blinkit
- Swiggy Instamart

Users can search for a product and instantly see which platform offers the lowest price.

---

# Project Goal

This project is a **beginner full-stack learning project** designed to demonstrate:

- web scraping
- async backend processing
- streaming APIs
- modern frontend development
- real-world system architecture

The system is **not intended as a production-scale service**.

---

# Features

Search grocery products by name

Enter delivery pincode

Compare prices across platforms

Group similar products automatically

Highlight the cheapest option

Stream results as they arrive

---

# Example Use Case

Search query:

milk  
pincode: 411001

Example results:

Product: Amul Milk 500ml

Blinkit → ₹28  
Instamart → ₹27 (cheapest)

---

# System Architecture

User  
↓  
Frontend (Next.js)  
↓  
Backend API (Python)  
↓  
Scrapers

Blinkit Scraper  
Instamart Scraper

↓

Similarity Matching

↓

Results streamed to frontend

---

# Tech Stack

Frontend

- Next.js

Backend

- Python

Scraping

- HTML parsing

Streaming

- Server-Sent Events (SSE)

Deployment

- Frontend → Vercel
- Backend → Free cloud VM

---

# Repository Structure

docs/
│
├ project-overview.md
│
├ architecture/
│ ├ system-architecture.md
│ ├ data-flow.md
│ └ deployment-architecture.md
│
├ backend/
│ ├ backend-spec.md
│ ├ scraper-architecture.md
│ ├ similarity-matching.md
│ └ api-design.md
│
├ frontend/
│ ├ frontend-spec.md
│ ├ ui-layout.md
│ └ streaming-ui-behavior.md
│
└ devops/
└ reliability-strategy.md

---

# How It Works

1. User enters product name and pincode.
2. Frontend sends request to backend API.
3. Backend launches async scraping tasks.
4. Scrapers extract product data from supported platforms.
5. Products are normalized and grouped using token similarity.
6. Results are streamed back to the frontend.
7. UI displays price comparisons.

---

# Product Matching

Products from different platforms may have slightly different names.

Example:

Amul Milk 500ml  
Amul Taaza Toned Milk 500ml

The system groups similar products using **token-based similarity matching**.

---

# Reliability Strategy

Scrapers implement a simple retry strategy.

If a scraper fails:

1 retry is attempted

If it still fails:

Partial results are returned to the user.

This ensures the application remains responsive even if one platform fails.

---

# Deployment

Frontend

Hosted on Vercel.

Backend

Hosted on a free cloud virtual machine.

This architecture avoids serverless time limits and allows scraping tasks to run reliably.

---

# Future Improvements

Additional platforms

Product image extraction

Price history tracking

Better similarity matching

Caching layer for faster responses

---

# Disclaimer

This project is for **educational purposes** and demonstrates scraping and price comparison techniques.

Platform structures may change and break scrapers.

---

# License

MIT License
