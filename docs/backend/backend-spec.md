# Backend Specification

## Overview

The backend provides the core functionality of the system.

It is responsible for scraping, data processing, and returning comparison results.

---

## Backend Responsibilities

Receive search requests

Trigger scraping tasks

Normalize product data

Perform similarity matching

Stream results to frontend

---

## Processing Flow

Receive search request

↓

Start scraper tasks

↓

Collect results

↓

Normalize product data

↓

Group similar products

↓

Send results to frontend
