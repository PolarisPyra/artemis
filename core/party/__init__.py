"""Game-agnostic multiplayer party broker.

Any Artemis title can opt into internet-mediated multiplayer by having its
cabinet-side bridge mod open a WebSocket to ``/ws/party`` with a ``game`` tag.
The broker holds lobby state in process memory, forwards opaque bytes between
paired cabinets, and tracks card-swipe presence. All cross-cabinet routing is
scoped by the ``game`` tag so lobbies from different titles never mix.

Exports:
    PartyBroker    — the broker class (state + mutations + WS handler + routes)
    Lobby, Member  — dataclasses used in responses
    PartyError     — raised by mutations on user-facing failures
    build_routes   — build the starlette Route list bound to a broker instance
"""
from core.party.broker import Lobby, Member, PartyBroker, PartyError
from core.party.routes import build_routes

__all__ = ["Lobby", "Member", "PartyBroker", "PartyError", "build_routes"]
