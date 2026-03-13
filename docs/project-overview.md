# Project Overview

## Purpose

This project is a web application that compares grocery prices across quick-commerce platforms.

Supported platforms:

- Blinkit
- Swiggy Instamart

Users can search for a product and see which platform offers the lowest price.

The system scrapes product data from supported platforms in real time and displays comparison results.

---

## Goals

This project is intended as a **beginner full-stack learning project**.

It demonstrates:

- web scraping
- async backend processing
- streaming APIs
- frontend UI development
- deployment architecture

The system is **not intended to scale to production workloads**.

---

## Core Features

Users can:

1. Enter a pincode
2. Search for a grocery item
3. View prices from multiple platforms
4. Identify the cheapest option

Example search:

milk  
pincode: 411001

---

## Key Technologies

Frontend:

- Next.js

Backend:

- Python

Deployment:

- Vercel (frontend)
- Free cloud VM (backend)

---

## Supported Platforms

Blinkit  
Swiggy Instamart

These platforms are scraped using HTML parsing techniques.

---

## High-Level System

User
↓
Frontend (Next.js)
↓
Backend API (Python)
↓
Scrapers

- Blinkit
- Instamart

Results are returned and displayed in grouped product cards.
