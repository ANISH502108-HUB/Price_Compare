# Scraper Architecture

## Overview

Each provider uses a dedicated adapter that runs behind a common `BaseScraper` transport layer.

Direct product-page HTML scraping is often blocked in deployment environments, so providers now use a two-step strategy:

1. Attempt provider JSON/XHR endpoints first.
2. Fallback to mirrored rendered search content (`r.jina.ai/http://...`) when direct endpoints are blocked.

## Modules

`backend/app/scrapers/base.py`

- shared transport helpers
- retry/backoff
- HTTP status classification
- session bootstrap hook

`backend/app/scrapers/blinkit_scraper.py`

- Blinkit endpoint adapter
- rendered-search fallback parsing
- payload-to-product normalization

`backend/app/scrapers/instamart_scraper.py`

- Instamart endpoint adapter
- rendered-search fallback parsing
- payload-to-product normalization

## Provider Flow

1. Initialize provider client with deployment-safe headers.
2. Warm session/cookies when provider requires bootstrap.
3. Call JSON endpoints with retry/backoff and status-based handling.
4. If blocked/contract mismatch, fetch mirrored rendered search content.
5. Parse payload into normalized products.
5. Return strict product schema:

- `platform`
- `name`
- `price`
- `url`

## Reliability and Streaming Compatibility

- Scraper errors are converted into provider-specific failures instead of breaking the stream.
- Worker + SSE behavior remains progressive:
  - per-platform result/error event
  - per-platform done signal
  - final completed event with grouped offers
