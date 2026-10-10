import base64
from datetime import datetime


def encode_cursor(created_at: datetime, id: str) -> str:
    raw = f"{created_at.isoformat()}|{id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str] | None:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts, id_ = raw.split("|", 1)
        return datetime.fromisoformat(ts), id_
    except Exception:
        return None
