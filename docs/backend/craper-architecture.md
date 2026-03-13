# Scraper Architecture

## Overview

Each platform uses a dedicated scraper module.

This ensures the system remains modular and easier to maintain.

---

## Scraper Modules

scrapers/

blinkit_scraper  
instamart_scraper

---

## Scraper Responsibilities

Send search request

Download page HTML

Parse product data

Extract fields:

platform  
name  
price  
url

---

## Example Output

platform: blinkit  
name: Amul Taaza Milk 500ml  
price: 28  
url: product link

---

## Advantages

Platform changes affect only one scraper module.

New platforms can be added easily by creating a new scraper module.
