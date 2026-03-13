# API Design

## Overview

The backend exposes a search endpoint used by the frontend.

---

## Endpoint

search

Input parameters:

item  
pincode

---

## Example Request

item: milk  
pincode: 411001

---

## Processing

1. receive request
2. start scraping tasks
3. stream results as they arrive

---

## Streaming

Results are sent using Server-Sent Events (SSE).

Example flow:

Blinkit results arrive

↓

Frontend displays Blinkit prices

↓

Instamart results arrive

↓

Frontend updates comparison cards
