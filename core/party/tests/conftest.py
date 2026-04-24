"""Shared fixtures for the party broker tests.

The broker accepts injected ``data`` so tests drive the real broker code path
without touching MySQL. A FakeWebSocket records every control frame for
assertion.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from core.party import PartyBroker


@dataclass
class FakeRow:
    _values: Dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def keys(self) -> List[str]:
        return list(self._values.keys())


class FakeUserData:
    def __init__(self) -> None:
        self.users: Dict[int, Dict[str, Any]] = {}

    def add(self, user_id: int, username: str) -> None:
        self.users[user_id] = {"id": user_id, "username": username}

    async def get_user(self, user_id: int):
        u = self.users.get(user_id)
        return FakeRow(u) if u else False


class FakeCardData:
    def __init__(self) -> None:
        self.cards: Dict[str, Dict[str, Any]] = {}

    def add(self, access_code: str, user_id: int) -> None:
        self.cards[access_code] = {"access_code": access_code, "user": user_id}

    async def get_card_by_access_code(self, access_code: str):
        c = self.cards.get(access_code)
        return FakeRow(c) if c else None


class FakeArcadeData:
    def __init__(self) -> None:
        self.machines: Dict[str, Dict[str, Any]] = {}

    def add(self, serial: str) -> None:
        self.machines[serial] = {"serial": serial}

    async def get_machine(self, serial: Optional[str] = None, id: Optional[int] = None):
        if serial is None:
            return None
        m = self.machines.get(serial)
        return FakeRow(m) if m else None


@dataclass
class FakeData:
    user: FakeUserData = field(default_factory=FakeUserData)
    card: FakeCardData = field(default_factory=FakeCardData)
    arcade: FakeArcadeData = field(default_factory=FakeArcadeData)


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent: List[Dict[str, Any]] = []
        self.closed: bool = False
        self.close_code: Optional[int] = None
        from starlette.websockets import WebSocketState

        self.client_state = WebSocketState.CONNECTED

    async def send_text(self, data: str) -> None:
        import json

        self.sent.append(json.loads(data))

    async def close(self, code: int = 1000) -> None:
        self.closed = True
        self.close_code = code
        from starlette.websockets import WebSocketState

        self.client_state = WebSocketState.DISCONNECTED

    def messages_of_type(self, t: str) -> List[Dict[str, Any]]:
        return [m for m in self.sent if m.get("type") == t]


@pytest.fixture
def fake_data() -> FakeData:
    return FakeData()


@pytest.fixture
def broker(fake_data: FakeData) -> PartyBroker:
    os.environ["LOBBY_SECRET"] = "test-lobby-secret"
    os.environ["COZYNET_API_KEY"] = "test-api-key"
    logger = logging.getLogger("test-party")
    logger.setLevel(logging.WARNING)
    return PartyBroker(core_cfg=None, logger=logger, data=fake_data)


@pytest.fixture
def fake_ws() -> FakeWebSocket:
    return FakeWebSocket()
