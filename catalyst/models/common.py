from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
