"""HTTP route tests against the game-scoped route set."""
from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from core.party import build_routes

GAME = "ongeki"
API_KEY = {"X-Cozynet-Api-Key": "test-api-key"}


@pytest.fixture
def client(broker):
    return TestClient(Starlette(routes=build_routes(broker)))


def _setup_user_at_cabinet(broker, fake_data, user_id, keychip, version, username, game=GAME):
    fake_data.user.add(user_id, username)
    fake_data.card.add(f"CARD{user_id}", user_id)
    fake_data.arcade.add(keychip)
    broker.keychip_to_version[(game, keychip)] = version
    broker.keychip_to_user[(game, keychip)] = user_id
    broker.user_to_keychip[(game, user_id)] = keychip


def test_create_rejects_missing_api_key(client):
    resp = client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1")
    assert resp.status_code == 401


def test_create_rejects_missing_on_behalf_of(client):
    resp = client.post(f"/internal/party/{GAME}/lobbies", headers=API_KEY)
    assert resp.status_code == 400
    assert resp.json()["error"] == "missing_on_behalf_of"


def test_create_rejects_no_cabinet(client):
    resp = client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY)
    assert resp.status_code == 400
    assert resp.json()["error"] == "not_at_cabinet"


def test_create_happy_path(client, broker, fake_data):
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    resp = client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["host_user_id"] == 1
    assert body["game"] == GAME
    assert body["game_version"] == "1.55"
    assert len(body["seats"]) == 1


def test_list_returns_all_open_lobbies_in_game(client, broker, fake_data):
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    _setup_user_at_cabinet(broker, fake_data, 2, "A69E01A0000002", "1.50", "bob")
    client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY)
    client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=2", headers=API_KEY)

    resp = client.get(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY)
    assert resp.status_code == 200
    hosts = sorted(l["host_user_id"] for l in resp.json()["lobbies"])
    assert hosts == [1, 2]


def test_list_is_game_scoped(client, broker, fake_data):
    """An ongeki lobby must not appear under /internal/party/chuni/lobbies."""
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice", game="ongeki")
    client.post("/internal/party/ongeki/lobbies?on_behalf_of=1", headers=API_KEY)
    resp = client.get("/internal/party/chuni/lobbies?on_behalf_of=1", headers=API_KEY)
    assert resp.status_code == 200
    assert resp.json()["lobbies"] == []


def test_join_leave_flow(client, broker, fake_data):
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    _setup_user_at_cabinet(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    created = client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY).json()
    lobby_id = created["id"]
    resp = client.post(f"/internal/party/{GAME}/lobbies/{lobby_id}/join?on_behalf_of=2", headers=API_KEY)
    assert resp.status_code == 200
    assert {s["user_id"] for s in resp.json()["seats"]} == {1, 2}

    resp = client.post(f"/internal/party/{GAME}/lobbies/{lobby_id}/leave?on_behalf_of=2", headers=API_KEY)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_kick_requires_host(client, broker, fake_data):
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    _setup_user_at_cabinet(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    created = client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY).json()
    lobby_id = created["id"]
    client.post(f"/internal/party/{GAME}/lobbies/{lobby_id}/join?on_behalf_of=2", headers=API_KEY)

    resp = client.post(
        f"/internal/party/{GAME}/lobbies/{lobby_id}/kick?on_behalf_of=2",
        headers=API_KEY,
        json={"seat": 1},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "not_host"


def test_presence_reflects_cabinet_binding(client, broker, fake_data):
    resp = client.get(f"/internal/party/{GAME}/presence?user_id=1", headers=API_KEY)
    assert resp.json()["at_cabinet"] is False
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    resp = client.get(f"/internal/party/{GAME}/presence?user_id=1", headers=API_KEY)
    body = resp.json()
    assert body["at_cabinet"] is True
    assert body["keychip"] == "A69E01A0000001"
    assert body["game_version"] == "1.55"
    assert body["game"] == GAME


def test_start_without_two_cabinets_fails(client, broker, fake_data):
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    created = client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY).json()
    resp = client.post(
        f"/internal/party/{GAME}/lobbies/{created['id']}/start?on_behalf_of=1",
        headers=API_KEY,
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "not_enough_cabinets"


def test_health_reports_counts(client, broker, fake_data):
    _setup_user_at_cabinet(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    client.post(f"/internal/party/{GAME}/lobbies?on_behalf_of=1", headers=API_KEY)
    # Health endpoint is not scoped per game — it aggregates across all games.
    resp = client.get("/internal/party/health", headers=API_KEY)
    body = resp.json()
    assert body["lobbies"] == 1
    assert body["bound_players"] == 1
