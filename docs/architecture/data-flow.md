# Data Flow

## Search Request Flow

1. User enters product name
2. User enters pincode
3. Frontend sends request to backend

Example request data:

item: milk  
pincode: 411001

---

## Backend Processing

The backend performs the following steps:

1. Receive request
2. Start async scraping tasks
3. Collect scraper results
4. Normalize product data
5. Group similar products
6. Stream results back to frontend

---

## Scraping Flow

Each scraper:

1. Sends request to platform search page
2. Downloads HTML
3. Parses product information
4. Extracts product data

---

## Result Flow

Scraper results are sent to the matching system.

Matching system groups products with similar names.

Example:

Amul Milk 500ml  
Amul Taaza Milk 500ml

These items are grouped together.

---

## Frontend Display

Results are displayed as grouped product cards.

Each group shows platform prices for similar products.
