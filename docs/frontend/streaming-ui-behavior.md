# Streaming UI Behavior

## Overview

Results are streamed from the backend as scraping completes.

This allows the UI to update progressively.

---

## Example Timeline

User searches: milk

0 seconds  
Search request sent

2 seconds  
Blinkit results received

4 seconds  
Instamart results received

---

## UI Updates

Blinkit card appears first.

Instamart card appears later.

The user sees results without waiting for all scrapers.
