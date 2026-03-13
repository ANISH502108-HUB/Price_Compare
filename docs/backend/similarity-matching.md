# Similarity Matching

## Overview

Products from different platforms may have slightly different names.

Example:

Amul Milk 500ml  
Amul Taaza Toned Milk 500ml

The system groups similar products together.

---

## Matching Strategy

Token matching.

Product names are split into words.

Example:

Amul Taaza Toned Milk 500ml

Tokens:

amul  
taaza  
toned  
milk  
500ml

---

## Similarity Logic

Products sharing important tokens are grouped together.

Example:

Amul Milk 500ml  
Amul Taaza Milk 500ml

Both contain:

amul  
milk  
500ml

These are grouped together.

---

## Output

Grouped product results are returned to the frontend.
