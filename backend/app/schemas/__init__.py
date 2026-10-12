from datetime import datetime, timezone
from pydantic import BaseModel


def _utc_isoformat(dt: datetime) -> str:
    """Serialize datetime as UTC ISO-8601 string ending in Z."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AppBaseModel(BaseModel):
    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: _utc_isoformat},
    }
