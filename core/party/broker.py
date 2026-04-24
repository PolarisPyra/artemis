"""In-process multiplayer party broker — game-agnostic core.

Every piece of state and every mutation is keyed by a ``game`` string, so one
broker instance can host lobbies for ONGEKI, Chunithm, Maimai, etc., in
isolation. Each game's bridge mod reports its ``game`` tag on the WebSocket
handshake and the broker enforces that cabinets can only be attached to
lobbies matching their game.

Persistence: none. Restart drops every active lobby. No new MySQL tables.
Existing `aime_card` and `machine` tables are used for identity resolution.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import jwt
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from core.config import CoreConfig
from core.data import Data

MAX_SEATS = 4


class PartyError(Exception):
    """Mutation failed for a reason the caller should surface to the user."""

    def __init__(self, code: str, status: int = 400, message: Optional[str] = None) -> None:
        super().__init__(message or code)
        self.code = code
        self.status = status
        self.message = message or code


@dataclass
class Member:
    seat: int
    user_id: int
    username: str


@dataclass
class Lobby:
    id: str
    game: str
    host_user_id: int
    game_version: str
    status: str = "waiting"  # waiting | active | closed
    members: Dict[int, Member] = field(default_factory=dict)
    cabinets: Dict[int, WebSocket] = field(default_factory=dict)
    watchers: Set[WebSocket] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "game": self.game,
            "host_user_id": self.host_user_id,
            "game_version": self.game_version,
            "status": self.status,
            "created_at": self.created_at,
            "seats": [
                {
                    "seat": m.seat,
                    "user_id": m.user_id,
                    "username": m.username,
                    "attached": m.user_id in self.cabinets,
                }
                for m in sorted(self.members.values(), key=lambda m: m.seat)
            ],
        }


@dataclass
class _CabinetKey:
    """Keychips are unique per-cabinet but a user could theoretically own
    cabinets for multiple games. Since a single cabinet only runs one game at
    a time we key presence on ``(game, keychip)`` to keep the mental model
    clean."""

    game: str
    keychip: str

    def __hash__(self) -> int:
        return hash((self.game, self.keychip))


class PartyBroker:
    def __init__(
        self,
        core_cfg: Optional[CoreConfig] = None,
        logger: Optional[logging.Logger] = None,
        data: Optional[Data] = None,
    ) -> None:
        self.core_cfg = core_cfg
        self.logger = logger or logging.getLogger("party")
        self.data = data if data is not None else (Data(core_cfg) if core_cfg is not None else None)

        self.lobby_secret = os.environ.get("LOBBY_SECRET", "")
        self.cozynet_api_key = os.environ.get("COZYNET_API_KEY", "")
        if not self.lobby_secret:
            self.logger.warning(
                "[party] LOBBY_SECRET is unset — web watcher JWT verification will reject all upgrades"
            )
        if not self.cozynet_api_key:
            self.logger.warning(
                "[party] COZYNET_API_KEY is unset — all /internal/party requests will be rejected"
            )

        # All state is keyed by (game, ...) so games never cross-contaminate.
        self.lobbies: Dict[str, Lobby] = {}
        # (game, user_id) -> lobby_id
        self.user_to_lobby: Dict[Tuple[str, int], str] = {}
        # (game, keychip) -> websocket waiting for a player swipe
        self.parked_cabinets: Dict[Tuple[str, str], WebSocket] = {}
        # (game, keychip) -> user_id of currently swiped player
        self.keychip_to_user: Dict[Tuple[str, str], int] = {}
        # (game, user_id) -> keychip they swiped at
        self.user_to_keychip: Dict[Tuple[str, int], str] = {}
        # (game, keychip) -> game version reported on WS connect
        self.keychip_to_version: Dict[Tuple[str, str], str] = {}
        # id(ws) -> (game, keychip)
        self.cabinet_to_key: Dict[int, Tuple[str, str]] = {}
        # id(ws) -> lobby_id or None (list topic). Scope string also encodes game.
        self.watcher_scope: Dict[int, Optional[str]] = {}
        # (game,) -> set of list-topic watcher WSes
        self.list_watchers: Dict[str, Set[WebSocket]] = {}

    # ==================================================================
    # Lobby mutations
    # ==================================================================

    async def create_lobby(self, game: str, on_behalf_of: int) -> Lobby:
        if (game, on_behalf_of) in self.user_to_lobby:
            raise PartyError("already_in_lobby", 409)
        keychip = self.user_to_keychip.get((game, on_behalf_of))
        if keychip is None:
            raise PartyError("not_at_cabinet", 400, "Swipe your card at a cabinet to create a lobby")
        version = self.keychip_to_version.get((game, keychip))
        if version is None:
            raise PartyError("no_cabinet_version", 400, "Cabinet has not reported a game version yet")

        username = await self._lookup_username(on_behalf_of)
        lobby = Lobby(
            id=uuid.uuid4().hex[:12],
            game=game,
            host_user_id=on_behalf_of,
            game_version=version,
        )
        lobby.members[on_behalf_of] = Member(seat=1, user_id=on_behalf_of, username=username)
        self.lobbies[lobby.id] = lobby
        self.user_to_lobby[(game, on_behalf_of)] = lobby.id
        self.logger.info(f"[party] {game} lobby {lobby.id} created by user {on_behalf_of} v{version}")

        cab_ws = self.parked_cabinets.pop((game, keychip), None)
        if cab_ws is not None:
            await self._attach_cabinet(lobby, on_behalf_of, cab_ws, role="host")

        await self._emit_list_event(game, {"type": "lobby_created", "lobby": lobby.to_json()})
        return lobby

    def list_lobbies(self, game: str) -> List[Dict[str, Any]]:
        """Return every open lobby for the given game. The UI filters/gates on
        the client side based on version compatibility — the broker is
        deliberately permissive here so users can see incompatible lobbies
        too (with Join disabled in the UI)."""
        out: List[Dict[str, Any]] = []
        for lobby in self.lobbies.values():
            if lobby.game != game:
                continue
            if lobby.status != "waiting":
                continue
            if len(lobby.members) >= MAX_SEATS:
                continue
            out.append(lobby.to_json())
        out.sort(key=lambda l: l["created_at"])
        return out

    async def join_lobby(self, game: str, lobby_id: str, on_behalf_of: int) -> Lobby:
        lobby = self._require_lobby(game, lobby_id)
        if (game, on_behalf_of) in self.user_to_lobby:
            raise PartyError("already_in_lobby", 409)
        if lobby.status != "waiting":
            raise PartyError("lobby_not_waiting", 409)
        if len(lobby.members) >= MAX_SEATS:
            raise PartyError("lobby_full", 409)

        keychip = self.user_to_keychip.get((game, on_behalf_of))
        if keychip is None:
            raise PartyError("not_at_cabinet", 400, "Swipe your card at a cabinet to join a lobby")
        version = self.keychip_to_version.get((game, keychip))
        if version is None:
            raise PartyError("no_cabinet_version", 400)
        if version != lobby.game_version:
            raise PartyError(
                "version_mismatch",
                409,
                f"Lobby is for {lobby.game_version}, your cabinet is running {version}",
            )

        seat = self._next_free_seat(lobby)
        username = await self._lookup_username(on_behalf_of)
        lobby.members[on_behalf_of] = Member(seat=seat, user_id=on_behalf_of, username=username)
        self.user_to_lobby[(game, on_behalf_of)] = lobby.id
        self.logger.info(f"[party] {game} user {on_behalf_of} joined lobby {lobby.id} seat {seat}")

        cab_ws = self.parked_cabinets.pop((game, keychip), None)
        if cab_ws is not None:
            await self._attach_cabinet(lobby, on_behalf_of, cab_ws, role="client")

        await self._emit_lobby_event(lobby, {"type": "member_joined", "lobby": lobby.to_json()})
        await self._emit_list_event(game, {"type": "lobby_updated", "lobby": lobby.to_json()})
        return lobby

    async def leave_lobby(self, game: str, lobby_id: str, on_behalf_of: int) -> None:
        lobby = self._require_lobby(game, lobby_id)
        if on_behalf_of not in lobby.members:
            raise PartyError("not_in_lobby", 404)
        if on_behalf_of == lobby.host_user_id:
            await self._close_lobby(lobby, reason="host_left")
        else:
            await self._remove_member(lobby, on_behalf_of, reason="left")

    async def kick_member(self, game: str, lobby_id: str, on_behalf_of: int, seat: int) -> None:
        lobby = self._require_lobby(game, lobby_id)
        if on_behalf_of != lobby.host_user_id:
            raise PartyError("not_host", 403)
        target = next((m for m in lobby.members.values() if m.seat == seat), None)
        if target is None:
            raise PartyError("seat_empty", 404)
        if target.user_id == lobby.host_user_id:
            raise PartyError("cannot_kick_host", 400)
        await self._remove_member(lobby, target.user_id, reason="kicked")

    async def start_lobby(self, game: str, lobby_id: str, on_behalf_of: int) -> Lobby:
        lobby = self._require_lobby(game, lobby_id)
        if on_behalf_of != lobby.host_user_id:
            raise PartyError("not_host", 403)
        if lobby.status != "waiting":
            raise PartyError("lobby_not_waiting", 409)
        attached = sum(1 for uid in lobby.members if uid in lobby.cabinets)
        if attached < 2:
            raise PartyError("not_enough_cabinets", 400, "At least two cabinets must be attached")

        lobby.status = "active"
        self.logger.info(f"[party] {game} lobby {lobby.id} started")
        for uid, ws in lobby.cabinets.items():
            role = "host" if uid == lobby.host_user_id else "client"
            await self._send_control(ws, {"type": "lobbyStart", "role": role})
        await self._emit_lobby_event(lobby, {"type": "lobby_started", "lobby": lobby.to_json()})
        await self._emit_list_event(game, {"type": "lobby_updated", "lobby": lobby.to_json()})
        return lobby

    # ==================================================================
    # Presence
    # ==================================================================

    async def bind_player(self, game: str, keychip: str, access_code: str) -> Optional[int]:
        card = await self.data.card.get_card_by_access_code(access_code) if self.data else None
        if not card:
            self.logger.warning(f"[party] {game} playerLogin from {keychip} with unknown access_code")
            return None
        user_id = int(card["user"])

        # Drop stale bindings on either side (same game only — a user swiping
        # at an ONGEKI cabinet doesn't affect their Chunithm presence).
        prev_keychip = self.user_to_keychip.get((game, user_id))
        if prev_keychip is not None and prev_keychip != keychip:
            await self._unbind_user(game, user_id, notify=True)
        prev_user = self.keychip_to_user.get((game, keychip))
        if prev_user is not None and prev_user != user_id:
            await self._unbind_user(game, prev_user, notify=True)

        self.keychip_to_user[(game, keychip)] = user_id
        self.user_to_keychip[(game, user_id)] = keychip
        self.logger.info(f"[party] {game} bound user {user_id} to keychip {keychip}")

        lobby_id = self.user_to_lobby.get((game, user_id))
        if lobby_id is not None:
            lobby = self.lobbies.get(lobby_id)
            cab_ws = self.parked_cabinets.pop((game, keychip), None)
            if lobby is not None and cab_ws is not None:
                role = "host" if user_id == lobby.host_user_id else "client"
                await self._attach_cabinet(lobby, user_id, cab_ws, role=role)

        await self._emit_presence(game, user_id)
        return user_id

    async def unbind_player(self, game: str, keychip: str) -> None:
        user_id = self.keychip_to_user.get((game, keychip))
        if user_id is None:
            return
        await self._unbind_user(game, user_id, notify=True)

    def presence_for(self, game: str, user_id: int) -> Dict[str, Any]:
        keychip = self.user_to_keychip.get((game, user_id))
        if keychip is None:
            return {"at_cabinet": False, "game": game}
        return {
            "at_cabinet": True,
            "game": game,
            "keychip": keychip,
            "game_version": self.keychip_to_version.get((game, keychip)),
        }

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _require_lobby(self, game: str, lobby_id: str) -> Lobby:
        lobby = self.lobbies.get(lobby_id)
        if lobby is None:
            raise PartyError("lobby_not_found", 404)
        if lobby.game != game:
            # Hide existence across games by returning the same error as "not found".
            raise PartyError("lobby_not_found", 404)
        return lobby

    def _next_free_seat(self, lobby: Lobby) -> int:
        taken = {m.seat for m in lobby.members.values()}
        for s in range(1, MAX_SEATS + 1):
            if s not in taken:
                return s
        raise PartyError("lobby_full", 409)

    async def _attach_cabinet(self, lobby: Lobby, user_id: int, ws: WebSocket, role: str) -> None:
        lobby.cabinets[user_id] = ws
        keychip = self.user_to_keychip.get((lobby.game, user_id), "")
        self.cabinet_to_key[id(ws)] = (lobby.game, keychip)
        member = lobby.members[user_id]
        await self._send_control(
            ws,
            {
                "type": "attached",
                "lobby_id": lobby.id,
                "seat": member.seat,
                "role": role,
            },
        )
        await self._emit_lobby_event(lobby, {"type": "cabinet_attached", "lobby": lobby.to_json()})

    async def _detach_cabinet(self, lobby: Lobby, user_id: int, reason: str) -> None:
        ws = lobby.cabinets.pop(user_id, None)
        if ws is None:
            return
        self.cabinet_to_key.pop(id(ws), None)
        await self._send_control(ws, {"type": "detached", "reason": reason})
        await self._emit_lobby_event(lobby, {"type": "cabinet_detached", "lobby": lobby.to_json()})

    async def _remove_member(self, lobby: Lobby, user_id: int, reason: str) -> None:
        member = lobby.members.pop(user_id, None)
        if member is None:
            return
        await self._detach_cabinet(lobby, user_id, reason=reason)
        self.user_to_lobby.pop((lobby.game, user_id), None)
        self.logger.info(f"[party] {lobby.game} user {user_id} removed from {lobby.id} ({reason})")
        await self._emit_lobby_event(lobby, {"type": "member_left", "lobby": lobby.to_json(), "reason": reason})
        await self._emit_list_event(lobby.game, {"type": "lobby_updated", "lobby": lobby.to_json()})

    async def _close_lobby(self, lobby: Lobby, reason: str) -> None:
        lobby.status = "closed"
        self.logger.info(f"[party] {lobby.game} lobby {lobby.id} closed ({reason})")
        for user_id in list(lobby.members.keys()):
            await self._detach_cabinet(lobby, user_id, reason=reason)
            self.user_to_lobby.pop((lobby.game, user_id), None)
        await self._emit_lobby_event(lobby, {"type": "lobby_closed", "lobby": lobby.to_json(), "reason": reason})
        await self._emit_list_event(lobby.game, {"type": "lobby_closed", "lobby_id": lobby.id})
        for ws in list(lobby.watchers):
            self.watcher_scope.pop(id(ws), None)
        lobby.watchers.clear()
        self.lobbies.pop(lobby.id, None)

    async def _unbind_user(self, game: str, user_id: int, notify: bool) -> None:
        keychip = self.user_to_keychip.pop((game, user_id), None)
        if keychip is not None:
            self.keychip_to_user.pop((game, keychip), None)
        lobby_id = self.user_to_lobby.get((game, user_id))
        if lobby_id is not None:
            lobby = self.lobbies.get(lobby_id)
            if lobby is not None:
                if user_id == lobby.host_user_id:
                    await self._close_lobby(lobby, reason="host_logout")
                else:
                    await self._remove_member(lobby, user_id, reason="logout")
        if notify:
            await self._emit_presence(game, user_id)

    # ==================================================================
    # WebSocket plumbing
    # ==================================================================

    async def _send_control(self, ws: WebSocket, msg: Dict[str, Any]) -> None:
        if ws.client_state != WebSocketState.CONNECTED:
            return
        try:
            await ws.send_text(json.dumps(msg))
        except Exception as e:
            self.logger.warning(f"[party] send_control failed: {e}")

    async def _emit_lobby_event(self, lobby: Lobby, event: Dict[str, Any]) -> None:
        dead: List[WebSocket] = []
        for ws in lobby.watchers:
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                dead.append(ws)
        for ws in dead:
            lobby.watchers.discard(ws)
            self.watcher_scope.pop(id(ws), None)

    async def _emit_list_event(self, game: str, event: Dict[str, Any]) -> None:
        watchers = self.list_watchers.get(game)
        if not watchers:
            return
        dead: List[WebSocket] = []
        for ws in watchers:
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                dead.append(ws)
        for ws in dead:
            watchers.discard(ws)
            self.watcher_scope.pop(id(ws), None)

    async def _emit_presence(self, game: str, user_id: int) -> None:
        event = {"type": "presence", "user_id": user_id, **self.presence_for(game, user_id)}
        await self._emit_list_event(game, event)
        lobby_id = self.user_to_lobby.get((game, user_id))
        if lobby_id is not None:
            lobby = self.lobbies.get(lobby_id)
            if lobby is not None:
                await self._emit_lobby_event(lobby, event)

    async def _lookup_username(self, user_id: int) -> str:
        if self.data is None:
            return f"user{user_id}"
        try:
            user = await self.data.user.get_user(user_id)
        except Exception:
            return f"user{user_id}"
        # UserData.get_user returns False on empty result, not None.
        if not user:
            return f"user{user_id}"
        try:
            username = user["username"]
        except (KeyError, TypeError):
            username = None
        return username or f"user{user_id}"

    async def _verify_keychip(self, keychip: str) -> bool:
        if self.data is None:
            return False
        try:
            machine = await self.data.arcade.get_machine(serial=keychip)
        except Exception as e:
            self.logger.error(f"[party] machine lookup failed for {keychip}: {e}")
            return False
        return machine is not None

    # ==================================================================
    # WebSocket handler
    # ==================================================================

    async def route_ws(self, ws: WebSocket) -> None:
        """Entry point wired by ``build_routes``. Dispatches by presence of
        keychip (cabinet bridge) or Authorization bearer (web watcher)."""
        qp = ws.query_params
        game = (qp.get("game") or "").strip()
        keychip = ws.headers.get("x-cabinet-keychip") or qp.get("keychip")
        auth = ws.headers.get("authorization") or ""
        token_qp = qp.get("token")

        if not game:
            await ws.close(code=4400)
            return

        if keychip:
            await self._handle_cabinet_ws(ws, game, keychip)
            return

        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            await self._handle_watcher_ws(ws, game, token)
            return
        if token_qp:
            await self._handle_watcher_ws(ws, game, token_qp)
            return

        await ws.close(code=4401)

    async def _handle_cabinet_ws(self, ws: WebSocket, game: str, keychip: str) -> None:
        version = ws.headers.get("x-cabinet-version") or ws.query_params.get("version") or "unknown"
        if not await self._verify_keychip(keychip):
            await ws.close(code=4403)
            return
        await ws.accept()
        self.keychip_to_version[(game, keychip)] = version
        self.logger.info(f"[party] {game} cabinet {keychip} connected v{version}")

        # If a different bridge for the same (game, keychip) is live, replace it.
        old = self.parked_cabinets.pop((game, keychip), None)
        if old is not None and old is not ws:
            try:
                await old.close(code=4000)
            except Exception:
                pass

        user_id = self.keychip_to_user.get((game, keychip))
        lobby: Optional[Lobby] = None
        if user_id is not None:
            lobby_id = self.user_to_lobby.get((game, user_id))
            if lobby_id is not None:
                lobby = self.lobbies.get(lobby_id)
        if lobby is not None and user_id is not None and user_id in lobby.members:
            role = "host" if user_id == lobby.host_user_id else "client"
            await self._attach_cabinet(lobby, user_id, ws, role=role)
        else:
            self.parked_cabinets[(game, keychip)] = ws
            await self._send_control(ws, {"type": "parked", "keychip": keychip})

        try:
            while True:
                raw = await ws.receive_text()
                await self._handle_cabinet_message(ws, game, keychip, raw)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            self.logger.warning(f"[party] cabinet {keychip} read error: {e}")
        finally:
            await self._cabinet_closed(ws, game, keychip)

    async def _handle_cabinet_message(self, ws: WebSocket, game: str, keychip: str, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except Exception:
            return
        if not isinstance(msg, dict):
            return
        kind = msg.get("type")
        if kind == "playerLogin":
            access_code = msg.get("access_code")
            if isinstance(access_code, str) and access_code:
                await self.bind_player(game, keychip, access_code)
        elif kind == "playerLogout":
            await self.unbind_player(game, keychip)
        elif kind == "data":
            await self._forward_data(game, keychip, msg)
        elif kind == "lobbyClosed":
            user_id = self.keychip_to_user.get((game, keychip))
            lobby_id = self.user_to_lobby.get((game, user_id)) if user_id is not None else None
            if lobby_id is not None:
                lobby = self.lobbies.get(lobby_id)
                if lobby is not None and user_id == lobby.host_user_id:
                    await self._close_lobby(lobby, reason="host_end")

    async def _forward_data(self, game: str, src_keychip: str, msg: Dict[str, Any]) -> None:
        src_user = self.keychip_to_user.get((game, src_keychip))
        if src_user is None:
            return
        lobby_id = self.user_to_lobby.get((game, src_user))
        if lobby_id is None:
            return
        lobby = self.lobbies.get(lobby_id)
        if lobby is None or lobby.status != "active":
            return
        payload = {"type": "data", "kind": msg.get("kind"), "src_port": msg.get("src_port"), "payload": msg.get("payload")}
        if src_user == lobby.host_user_id:
            for uid, peer in lobby.cabinets.items():
                if uid == src_user:
                    continue
                await self._send_control(peer, payload)
        else:
            host_ws = lobby.cabinets.get(lobby.host_user_id)
            if host_ws is not None:
                await self._send_control(host_ws, payload)

    async def _cabinet_closed(self, ws: WebSocket, game: str, keychip: str) -> None:
        self.logger.info(f"[party] {game} cabinet {keychip} disconnected")
        if self.parked_cabinets.get((game, keychip)) is ws:
            self.parked_cabinets.pop((game, keychip), None)
        user_id = self.keychip_to_user.get((game, keychip))
        if user_id is not None:
            lobby_id = self.user_to_lobby.get((game, user_id))
            if lobby_id is not None:
                lobby = self.lobbies.get(lobby_id)
                if lobby is not None and lobby.cabinets.get(user_id) is ws:
                    await self._detach_cabinet(lobby, user_id, reason="cabinet_disconnected")
        self.cabinet_to_key.pop(id(ws), None)
        if ws.client_state != WebSocketState.DISCONNECTED:
            try:
                await ws.close()
            except Exception:
                pass

    async def _handle_watcher_ws(self, ws: WebSocket, game: str, token: str) -> None:
        if not self.lobby_secret:
            await ws.close(code=4403)
            return
        try:
            payload = jwt.decode(token, self.lobby_secret, algorithms=["HS256"])
        except jwt.PyJWTError as e:
            self.logger.info(f"[party] watcher rejected: {e}")
            await ws.close(code=4401)
            return
        scope = payload.get("scope")
        user_id = payload.get("user_id")
        token_game = payload.get("game")
        if not isinstance(scope, str) or not isinstance(user_id, int):
            await ws.close(code=4401)
            return
        # JWT must be for the same game as the URL query param. Prevents
        # cross-game scope confusion if LOBBY_SECRET is ever compromised for
        # one frontend but the attacker tries to use it against a different
        # game's lobbies.
        if token_game and token_game != game:
            await ws.close(code=4403)
            return

        await ws.accept()
        lobby_id: Optional[str] = None
        if scope == "list":
            self.list_watchers.setdefault(game, set()).add(ws)
            self.watcher_scope[id(ws)] = None
        elif scope.startswith("lobby:"):
            lobby_id = scope.split(":", 1)[1]
            lobby = self.lobbies.get(lobby_id)
            if lobby is None or lobby.game != game:
                await self._send_control(ws, {"type": "error", "code": "lobby_not_found"})
                await ws.close()
                return
            lobby.watchers.add(ws)
            self.watcher_scope[id(ws)] = lobby_id
            await self._send_control(ws, {"type": "snapshot", "lobby": lobby.to_json()})
        else:
            await ws.close(code=4401)
            return

        try:
            while True:
                _ = await ws.receive_text()
        except WebSocketDisconnect:
            pass
        except Exception as e:
            self.logger.debug(f"[party] watcher read end: {e}")
        finally:
            await self._watcher_closed(ws, game, lobby_id)

    async def _watcher_closed(self, ws: WebSocket, game: str, lobby_id: Optional[str]) -> None:
        self.watcher_scope.pop(id(ws), None)
        if lobby_id is None:
            watchers = self.list_watchers.get(game)
            if watchers is not None:
                watchers.discard(ws)
        else:
            lobby = self.lobbies.get(lobby_id)
            if lobby is not None:
                lobby.watchers.discard(ws)
        if ws.client_state != WebSocketState.DISCONNECTED:
            try:
                await ws.close()
            except Exception:
                pass
