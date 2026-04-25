"""Unit tests for PartyBroker mutations — pure in-memory, no DB, no WS.

Tests use ``game="ongeki"`` for most cases; a dedicated isolation test covers
cross-game separation (a user in an ongeki lobby is unaffected by chunithm
state and vice versa).
"""
from __future__ import annotations

import pytest

from core.party import PartyError

GAME = "ongeki"


pytestmark = pytest.mark.asyncio


async def _swipe_in(broker, fake_data, user_id: int, keychip: str, version: str, username: str, game: str = GAME):
    fake_data.user.add(user_id, username)
    fake_data.card.add(f"CARD{user_id:09d}", user_id)
    fake_data.arcade.add(keychip)
    broker.keychip_to_version[(game, keychip)] = version
    await broker.bind_player(game, keychip, f"CARD{user_id:09d}")


async def test_create_lobby_happy_path(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    lobby = await broker.create_lobby(GAME, 1)
    assert lobby.host_user_id == 1
    assert lobby.game == GAME
    assert lobby.game_version == "1.55"
    assert lobby.members[1].seat == 1
    assert broker.user_to_lobby[(GAME, 1)] == lobby.id


async def test_create_lobby_requires_cabinet_presence(broker):
    with pytest.raises(PartyError) as exc:
        await broker.create_lobby(GAME, 42)
    assert exc.value.code == "not_at_cabinet"


async def test_create_lobby_rejects_double_create(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await broker.create_lobby(GAME, 1)
    with pytest.raises(PartyError) as exc:
        await broker.create_lobby(GAME, 1)
    assert exc.value.code == "already_in_lobby"


async def test_join_lobby_happy_path(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    assert set(lobby.members.keys()) == {1, 2}
    assert lobby.members[2].seat == 2


async def test_join_lobby_version_mismatch(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.50", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    with pytest.raises(PartyError) as exc:
        await broker.join_lobby(GAME, lobby.id, 2)
    assert exc.value.code == "version_mismatch"


async def test_join_lobby_full(broker, fake_data):
    for i in range(1, 6):
        await _swipe_in(broker, fake_data, i, f"A69E01A000000{i}", "1.55", f"p{i}")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    await broker.join_lobby(GAME, lobby.id, 3)
    await broker.join_lobby(GAME, lobby.id, 4)
    with pytest.raises(PartyError) as exc:
        await broker.join_lobby(GAME, lobby.id, 5)
    assert exc.value.code == "lobby_full"


async def test_join_lobby_unknown(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    with pytest.raises(PartyError) as exc:
        await broker.join_lobby(GAME, "does-not-exist", 1)
    assert exc.value.code == "lobby_not_found"


async def test_leave_member(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    await broker.leave_lobby(GAME, lobby.id, 2)
    assert 2 not in lobby.members
    assert (GAME, 2) not in broker.user_to_lobby
    assert lobby.id in broker.lobbies


async def test_leave_host_closes_lobby(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    lobby_id = lobby.id
    await broker.leave_lobby(GAME, lobby_id, 1)
    assert lobby_id not in broker.lobbies
    assert (GAME, 1) not in broker.user_to_lobby
    assert (GAME, 2) not in broker.user_to_lobby


async def test_kick_requires_host(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    await _swipe_in(broker, fake_data, 3, "A69E01A0000003", "1.55", "charlie")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    await broker.join_lobby(GAME, lobby.id, 3)
    with pytest.raises(PartyError) as exc:
        await broker.kick_member(GAME, lobby.id, 2, seat=3)
    assert exc.value.code == "not_host"


async def test_kick_removes_member(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    await broker.kick_member(GAME, lobby.id, 1, seat=2)
    assert 2 not in lobby.members


async def test_cannot_kick_host(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    with pytest.raises(PartyError) as exc:
        await broker.kick_member(GAME, lobby.id, 1, seat=1)
    assert exc.value.code == "cannot_kick_host"


async def test_bind_player_unknown_access_code(broker, fake_data):
    fake_data.arcade.add("A69E01A0000001")
    broker.keychip_to_version[(GAME, "A69E01A0000001")] = "1.55"
    result = await broker.bind_player(GAME, "A69E01A0000001", "BOGUS")
    assert result is None


async def test_bind_player_attaches_parked_cabinet(broker, fake_data, fake_ws):
    fake_data.user.add(1, "alice")
    fake_data.card.add("CARD000000001", 1)
    fake_data.arcade.add("A69E01A0000001")
    broker.keychip_to_version[(GAME, "A69E01A0000001")] = "1.55"
    await broker.bind_player(GAME, "A69E01A0000001", "CARD000000001")
    lobby = await broker.create_lobby(GAME, 1)
    broker.parked_cabinets[(GAME, "A69E01A0000001")] = fake_ws
    await broker.bind_player(GAME, "A69E01A0000001", "CARD000000001")
    assert lobby.cabinets.get(1) is fake_ws
    assert fake_ws.messages_of_type("attached")


async def test_list_returns_all_open_lobbies_for_game(broker, fake_data):
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.50", "bob")
    a = await broker.create_lobby(GAME, 1)
    b = await broker.create_lobby(GAME, 2)
    out = broker.list_lobbies(GAME)
    assert sorted(l["id"] for l in out) == sorted([a.id, b.id])


async def test_cross_game_isolation(broker, fake_data):
    """Two users each hosting a lobby in different games must not see each
    other's state."""
    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice", game="ongeki")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "2.30", "bob", game="chuni")
    ongeki_lobby = await broker.create_lobby("ongeki", 1)
    chuni_lobby = await broker.create_lobby("chuni", 2)

    assert [l["id"] for l in broker.list_lobbies("ongeki")] == [ongeki_lobby.id]
    assert [l["id"] for l in broker.list_lobbies("chuni")] == [chuni_lobby.id]

    # Attempting to join the wrong game's lobby via the other game's tag is
    # indistinguishable from "not found" (prevents cross-game enumeration).
    await _swipe_in(broker, fake_data, 3, "A69E01A0000003", "1.55", "charlie", game="ongeki")
    with pytest.raises(PartyError) as exc:
        await broker.join_lobby("ongeki", chuni_lobby.id, 3)
    assert exc.value.code == "lobby_not_found"


async def test_version_swap_kicks_previous_user(broker, fake_data):
    fake_data.user.add(1, "alice")
    fake_data.card.add("CARD1", 1)
    fake_data.arcade.add("A69E01A0000001")
    broker.keychip_to_version[(GAME, "A69E01A0000001")] = "1.55"
    await broker.bind_player(GAME, "A69E01A0000001", "CARD1")

    fake_data.user.add(2, "bob")
    fake_data.card.add("CARD2", 2)
    await broker.bind_player(GAME, "A69E01A0000001", "CARD2")
    assert broker.keychip_to_user[(GAME, "A69E01A0000001")] == 2
    assert (GAME, 1) not in broker.user_to_keychip


async def test_cabinet_disconnect_unbinds_player_and_leaves_lobby(broker, fake_data):
    """Game termination (cabinet WS dropping) clears presence AND removes the
    user from any lobby. Distinct from a simple cabinet detach which would
    leave the seat as 'pending'."""
    from core.party.tests.conftest import FakeWebSocket

    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)

    # Bob's cabinet has a live WS attached.
    bob_ws = FakeWebSocket()
    lobby.cabinets[2] = bob_ws
    broker.parked_cabinets[(GAME, "A69E01A0000002")] = bob_ws

    # Game terminates (WS closes).
    await broker._cabinet_closed(bob_ws, GAME, "A69E01A0000002")

    # Bob is no longer in the lobby (full leave, not just detach).
    assert 2 not in lobby.members
    assert (GAME, 2) not in broker.user_to_lobby
    # Presence cleared — Bob is no longer "at a cabinet".
    assert (GAME, 2) not in broker.user_to_keychip
    assert (GAME, "A69E01A0000002") not in broker.keychip_to_user
    # Alice is unaffected.
    assert 1 in lobby.members


async def test_host_cabinet_disconnect_closes_lobby(broker, fake_data):
    """If the host's cabinet terminates, the lobby is closed (not just left
    with an absent host)."""
    from core.party.tests.conftest import FakeWebSocket

    await _swipe_in(broker, fake_data, 1, "A69E01A0000001", "1.55", "alice")
    await _swipe_in(broker, fake_data, 2, "A69E01A0000002", "1.55", "bob")
    lobby = await broker.create_lobby(GAME, 1)
    await broker.join_lobby(GAME, lobby.id, 2)
    lobby_id = lobby.id

    alice_ws = FakeWebSocket()
    lobby.cabinets[1] = alice_ws
    broker.parked_cabinets[(GAME, "A69E01A0000001")] = alice_ws

    await broker._cabinet_closed(alice_ws, GAME, "A69E01A0000001")

    assert lobby_id not in broker.lobbies
    assert (GAME, 1) not in broker.user_to_lobby
    assert (GAME, 2) not in broker.user_to_lobby
    assert (GAME, "A69E01A0000001") not in broker.keychip_to_user
