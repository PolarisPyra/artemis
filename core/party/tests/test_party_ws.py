"""WebSocket handshake + frame-routing tests, game-scoped."""
from __future__ import annotations

import time

import jwt
import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from core.party import build_routes

GAME = "ongeki"
API_KEY = "test-api-key"


@pytest.fixture
def app(broker):
    return Starlette(routes=build_routes(broker))


def _seed_user(broker, fake_data, user_id, keychip, version, username, game=GAME):
    fake_data.user.add(user_id, username)
    fake_data.card.add(f"CARD{user_id}", user_id)
    fake_data.arcade.add(keychip)
    broker.keychip_to_version[(game, keychip)] = version
    broker.keychip_to_user[(game, keychip)] = user_id
    broker.user_to_keychip[(game, user_id)] = keychip


def test_cabinet_ws_rejects_unknown_keychip(app):
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/ws/party?game={GAME}",
            headers={"X-Cabinet-Keychip": "A69E01ANOTREAL1", "X-Cabinet-Version": "1.55"},
        ):
            pass


def test_cabinet_ws_rejects_missing_game(app, fake_data):
    fake_data.arcade.add("A69E01A0000001")
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(
            "/ws/party",
            headers={"X-Cabinet-Keychip": "A69E01A0000001", "X-Cabinet-Version": "1.55"},
        ):
            pass


def test_cabinet_ws_accepts_known_keychip_and_parks(app, broker, fake_data):
    fake_data.arcade.add("A69E01A0000001")
    client = TestClient(app)
    with client.websocket_connect(
        f"/ws/party?game={GAME}",
        headers={"X-Cabinet-Keychip": "A69E01A0000001", "X-Cabinet-Version": "1.55"},
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "parked"
        assert msg["keychip"] == "A69E01A0000001"
    assert (GAME, "A69E01A0000001") not in broker.parked_cabinets


def test_cabinet_player_login_binds_to_existing_lobby(app, broker, fake_data):
    _seed_user(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    client = TestClient(app)
    resp = client.post(
        f"/internal/party/{GAME}/lobbies?on_behalf_of=1",
        headers={"X-Cozynet-Api-Key": API_KEY},
    )
    assert resp.status_code == 200
    lobby_id = resp.json()["id"]

    fake_data.user.add(2, "bob")
    fake_data.card.add("CARD2", 2)
    fake_data.arcade.add("A69E01A0000002")

    with client.websocket_connect(
        f"/ws/party?game={GAME}",
        headers={"X-Cabinet-Keychip": "A69E01A0000002", "X-Cabinet-Version": "1.55"},
    ) as bob_ws:
        assert bob_ws.receive_json()["type"] == "parked"
        join = client.post(
            f"/internal/party/{GAME}/lobbies/{lobby_id}/join?on_behalf_of=2",
            headers={"X-Cozynet-Api-Key": API_KEY},
        )
        assert join.status_code == 400
        assert join.json()["error"] == "not_at_cabinet"

        bob_ws.send_json({"type": "playerLogin", "access_code": "CARD2"})
        join = client.post(
            f"/internal/party/{GAME}/lobbies/{lobby_id}/join?on_behalf_of=2",
            headers={"X-Cozynet-Api-Key": API_KEY},
        )
        assert join.status_code == 200
        attached = bob_ws.receive_json()
        assert attached["type"] == "attached"
        assert attached["seat"] == 2
        assert attached["role"] == "client"


def test_watcher_ws_rejects_bad_jwt(app):
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/ws/party?game={GAME}",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        ):
            pass


def test_watcher_ws_rejects_cross_game_token(app):
    token = jwt.encode(
        {"user_id": 1, "scope": "list", "game": "chuni", "exp": int(time.time()) + 60},
        "test-lobby-secret",
        algorithm="HS256",
    )
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/ws/party?game={GAME}",
            headers={"Authorization": f"Bearer {token}"},
        ):
            pass


def test_watcher_lobby_scope_receives_snapshot(app, broker, fake_data):
    _seed_user(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    client = TestClient(app)
    resp = client.post(
        f"/internal/party/{GAME}/lobbies?on_behalf_of=1",
        headers={"X-Cozynet-Api-Key": API_KEY},
    )
    lobby_id = resp.json()["id"]

    token = jwt.encode(
        {"user_id": 1, "scope": f"lobby:{lobby_id}", "game": GAME, "exp": int(time.time()) + 60},
        "test-lobby-secret",
        algorithm="HS256",
    )
    with client.websocket_connect(
        f"/ws/party?game={GAME}", headers={"Authorization": f"Bearer {token}"}
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "snapshot"
        assert msg["lobby"]["id"] == lobby_id
        assert msg["lobby"]["game"] == GAME
