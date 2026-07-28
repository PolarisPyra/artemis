"""Protocol objects shared by Konami middleware and title handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EamuseBody:
    data: dict[str, Any]
    raw: bytes
    module: str
    method: str
    model: str
    encrypted: bool = False
    compressed: bool = False
    kencoded: bool = False
    encoding: str = "utf-8"


@dataclass
class EamuseInfo:
    game_code: str
    module: str
    method: str
    model: str
    client_ip: str = ""
    host: str = ""
    protocol: str = "http"
    proxy: bool = False


@dataclass
class EamuseResponse:
    content: dict[str, Any] = field(default_factory=dict)
    status: int = 0
    root_name: str = ""
    encoding: str | None = None
    compress: bool | None = None
    encrypt: bool | None = None
