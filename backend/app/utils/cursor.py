"""
Opaque cursor encoding/decoding for keyset pagination.

Cursor format: base64url( JSON({"ts": <ISO-8601 datetime>, "id": <int>}) )

The cursor encodes the (created_at, id) pair of the LAST item on the current
page. The next page query uses this pair to continue from exactly that position
in the (created_at DESC, id DESC) ordering without any row skips or duplicates.

Stripping the base64 padding ("=") keeps the cursor URL-safe without additional
percent-encoding.
"""

import base64
import json
import logging
from datetime import datetime, timezone

from app.core.exceptions import InvalidCursorError

logger = logging.getLogger("codevector.cursor")


def encode_cursor(created_at: datetime, product_id: int) -> str:
    """Encode a (created_at, id) position as an opaque base64url string."""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    payload = json.dumps(
        {"ts": created_at.isoformat(), "id": product_id},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    """
    Decode an opaque cursor string into a (created_at, id) tuple.

    Raises InvalidCursorError if the cursor is malformed or tampered.
    """
    try:
        # Restore stripped padding
        padding = (4 - len(cursor) % 4) % 4
        padded = cursor + "=" * padding
        raw = base64.urlsafe_b64decode(padded.encode())
        data = json.loads(raw)

        ts = datetime.fromisoformat(data["ts"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        product_id = int(data["id"])
        return ts, product_id
    except Exception as exc:
        logger.debug("Failed to decode cursor %r: %s", cursor, exc)
        raise InvalidCursorError() from exc
