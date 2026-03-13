# Reliability Strategy

## Overview

Scrapers may occasionally fail due to network issues or website changes.

The system implements a retry and fallback strategy.

---

## Retry Logic

If a scraper fails:

retry request once

If it fails again:

return partial results.

---

## Example

Blinkit scraper succeeds.

Instamart scraper fails.

User still sees Blinkit results.

---

## Benefits

Users receive results even when one platform fails.

The system remains responsive despite scraper errors.
