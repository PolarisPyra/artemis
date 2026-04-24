"""Starlette route wiring for the game-agnostic party broker.

Routes are mounted at the Artemis root (via ``core/app.py``) with the ``game``
tag as a path parameter — e.g. ``/internal/party/ongeki/lobbies``. The
WebSocket endpoint is a single ``/ws/party`` that takes ``?game=...``.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, WebSocketRoute

from core.party.broker import PartyBroker, PartyError


def _check_internal_auth(broker: PartyBroker, request: Request) -> Optional[Response]:
    if not broker.cozynet_api_key:
        return JSONResponse({"error": "party_disabled"}, status_code=503)
    presented = request.headers.get("x-cozynet-api-key") or ""
    if presented != broker.cozynet_api_key:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return None


def _require_on_behalf_of(request: Request) -> Tuple[Optional[int], Optional[Response]]:
    raw = request.query_params.get("on_behalf_of")
    if raw is None:
        return None, JSONResponse({"error": "missing_on_behalf_of"}, status_code=400)
    try:
        return int(raw), None
    except ValueError:
        return None, JSONResponse({"error": "invalid_on_behalf_of"}, status_code=400)


def _game(request: Request) -> str:
    return request.path_params.get("game", "")


def build_routes(broker: PartyBroker) -> List[Route]:
    """Return the full set of starlette routes bound to this broker instance.

    Caller is responsible for adding these to the app's route list.
    """

    async def route_ws(ws):
        await broker.route_ws(ws)

    async def route_create_lobby(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        user_id, deny = _require_on_behalf_of(request)
        if deny is not None:
            return deny
        try:
            lobby = await broker.create_lobby(_game(request), user_id)
        except PartyError as e:
            return JSONResponse({"error": e.code, "message": e.message}, status_code=e.status)
        return JSONResponse(lobby.to_json())

    async def route_list_lobbies(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        _, deny = _require_on_behalf_of(request)
        if deny is not None:
            return deny
        return JSONResponse({"lobbies": broker.list_lobbies(_game(request))})

    async def route_join_lobby(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        user_id, deny = _require_on_behalf_of(request)
        if deny is not None:
            return deny
        try:
            lobby = await broker.join_lobby(_game(request), request.path_params.get("id", ""), user_id)
        except PartyError as e:
            return JSONResponse({"error": e.code, "message": e.message}, status_code=e.status)
        return JSONResponse(lobby.to_json())

    async def route_leave_lobby(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        user_id, deny = _require_on_behalf_of(request)
        if deny is not None:
            return deny
        try:
            await broker.leave_lobby(_game(request), request.path_params.get("id", ""), user_id)
        except PartyError as e:
            return JSONResponse({"error": e.code, "message": e.message}, status_code=e.status)
        return JSONResponse({"ok": True})

    async def route_start_lobby(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        user_id, deny = _require_on_behalf_of(request)
        if deny is not None:
            return deny
        try:
            lobby = await broker.start_lobby(_game(request), request.path_params.get("id", ""), user_id)
        except PartyError as e:
            return JSONResponse({"error": e.code, "message": e.message}, status_code=e.status)
        return JSONResponse(lobby.to_json())

    async def route_kick_member(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        user_id, deny = _require_on_behalf_of(request)
        if deny is not None:
            return deny
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid_body"}, status_code=400)
        seat = body.get("seat") if isinstance(body, dict) else None
        if not isinstance(seat, int):
            return JSONResponse({"error": "invalid_seat"}, status_code=400)
        try:
            await broker.kick_member(_game(request), request.path_params.get("id", ""), user_id, seat)
        except PartyError as e:
            return JSONResponse({"error": e.code, "message": e.message}, status_code=e.status)
        return JSONResponse({"ok": True})

    async def route_presence(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        raw = request.query_params.get("user_id")
        if raw is None:
            return JSONResponse({"error": "missing_user_id"}, status_code=400)
        try:
            uid = int(raw)
        except ValueError:
            return JSONResponse({"error": "invalid_user_id"}, status_code=400)
        return JSONResponse(broker.presence_for(_game(request), uid))

    async def route_health(request: Request) -> Response:
        deny = _check_internal_auth(broker, request)
        if deny is not None:
            return deny
        return JSONResponse(
            {
                "lobbies": len(broker.lobbies),
                "parked_cabinets": len(broker.parked_cabinets),
                "bound_players": len(broker.keychip_to_user),
                "watchers": len(broker.watcher_scope),
            }
        )

    return [
        WebSocketRoute("/ws/party", route_ws),
        Route("/internal/party/{game:str}/lobbies", route_list_lobbies, methods=["GET"]),
        Route("/internal/party/{game:str}/lobbies", route_create_lobby, methods=["POST"]),
        Route("/internal/party/{game:str}/lobbies/{id:str}/join", route_join_lobby, methods=["POST"]),
        Route("/internal/party/{game:str}/lobbies/{id:str}/leave", route_leave_lobby, methods=["POST"]),
        Route("/internal/party/{game:str}/lobbies/{id:str}/start", route_start_lobby, methods=["POST"]),
        Route("/internal/party/{game:str}/lobbies/{id:str}/kick", route_kick_member, methods=["POST"]),
        Route("/internal/party/{game:str}/presence", route_presence, methods=["GET"]),
        Route("/internal/party/health", route_health, methods=["GET"]),
    ]
