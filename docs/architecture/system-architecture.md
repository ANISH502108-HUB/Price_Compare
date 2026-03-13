# System Architecture

## Overview

The application follows a simple client-server architecture.

Frontend handles the user interface while the backend performs scraping and product comparison.

---

## Architecture Diagram

User
↓
Next.js Frontend
↓
Backend API
↓
Async Scraper Tasks

Blinkit Scraper  
Instamart Scraper

↓

Similarity Matching

↓

Results returned to frontend

---

## Components

### Frontend

Responsibilities:

- display search interface
- send search requests
- receive streaming results
- display comparison cards

---

### Backend API

Responsibilities:

- receive search queries
- trigger scrapers
- normalize product data
- group similar products
- stream results to frontend

---

### Scrapers

Separate scraper modules are used for each platform.

blinkit_scraper  
instamart_scraper

Each scraper extracts:

- product name
- price
- product URL
