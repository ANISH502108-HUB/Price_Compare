from __future__ import annotations

import re

from fastapi import APIRouter, Query
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.services.search_service import stream_search_events

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/search")
async def search(
    item: str = Query(..., min_length=1, max_length=120),
    pincode: str = Query(..., min_length=1, max_length=12),
) -> StreamingResponse:
    normalized_item = item.strip()
    normalized_pincode = pincode.strip()

    if not normalized_item:
        raise HTTPException(status_code=422, detail="item must not be empty")

    if not re.fullmatch(r"\d{6}", normalized_pincode):
        raise HTTPException(status_code=422, detail="pincode must be a 6-digit number")

    stream = stream_search_events(item=normalized_item, pincode=normalized_pincode)
    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(stream, media_type="text/event-stream", headers=headers)
