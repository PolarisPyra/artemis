"""Starlette application adapter for the Konami service."""

from __future__ import annotations

import logging
import struct
from typing import Callable, Iterable
from xml.etree.ElementTree import ParseError

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.applications import Starlette

from .encryption import KonmaiEncrypt
from .kbin import decode as kbin_decode, encode as kbin_encode, is_kbin
from .lzkn import deflate, inflate
from .protocol import EamuseBody, EamuseInfo, EamuseResponse
from .router import EamuseRouter
from .xml import data_to_xml, detect_xml_encoding, xml_to_data


class KonamiServlet:
    def __init__(self, route_sets: Iterable[Callable[[EamuseRouter], None]] = ()) -> None:
        self.logger = logging.getLogger("konami")
        self.router = EamuseRouter()
        for register_routes in route_sets:
            register_routes(self.router)

    def get_routes(self) -> list[Route]:
        # Konami clients commonly post to /, while services discovered through
        # services.get may use arbitrary module paths.  The catch-all route is
        # therefore intentional.
        return [
            Route("/", self.health, methods=["GET"]),
            Route("/keepalive", self.keepalive, methods=["GET"]),
            Route("/{path:path}", self.handle, methods=["POST"]),
        ]

    async def health(self, request: Request) -> Response:
        return Response(
            "<!doctype html><html><head><title>Konami Service</title></head>"
            "<body><h1>Service OK</h1></body></html>",
            media_type="text/html",
        )

    async def keepalive(self, request: Request) -> Response:
        return Response("OK", media_type="text/plain")

    async def dispatch_webui_event(
        self, game_code: str, name: str, data: dict
    ) -> bool:
        """Dispatch a title WebUI event without exposing an unauthenticated route."""
        result = self.router.dispatch_webui(game_code, name, data)
        if result is None:
            return False
        await result
        return True

    async def handle(self, request: Request) -> Response:
        raw = await request.body()
        body = raw
        encrypted = bool(request.headers.get("x-eamuse-info"))
        if encrypted:
            body = KonmaiEncrypt(request.headers["x-eamuse-info"]).crypt(body)

        compressed = request.headers.get("x-compress", "none") == "lz77"
        if compressed:
            body = inflate(body)

        try:
            if is_kbin(body):
                data, request_encoding = kbin_decode(body)
                kencoded = True
            else:
                request_encoding = detect_xml_encoding(body)
                data = xml_to_data(body, request_encoding)
                kencoded = False
            call = data.get("call", {})
            module, method = self._find_call(call)
            model = call.get("@attr", {}).get("model", "")
            game_code = model.split(":", 1)[0]
        except (
            ValueError,
            UnicodeDecodeError,
            IndexError,
            ParseError,
            struct.error,
        ) as exc:
            self.logger.warning("Unable to decode e-amusement request: %s", exc)
            return Response(status_code=404)

        forwarded_host = request.headers.get("x-forwarded-host")
        forwarded_proto = request.headers.get("x-forwarded-proto")
        forwarded_port = request.headers.get("x-forwarded-port")
        info = EamuseInfo(
            game_code=game_code,
            module=module,
            method=method,
            model=model,
            client_ip=request.client.host if request.client else "",
            host=forwarded_host or request.headers.get("host", ""),
            protocol=forwarded_proto or request.url.scheme,
            proxy=bool(forwarded_host or forwarded_proto or forwarded_port),
        )
        parsed = EamuseBody(
            data=data,
            raw=raw,
            module=module,
            method=method,
            model=model,
            encrypted=encrypted,
            compressed=compressed,
            kencoded=kencoded,
            encoding=request_encoding,
        )
        result = EamuseResponse(
            root_name=module, compress=compressed, encrypt=encrypted
        )
        await self.router.dispatch(parsed, info, result)
        self.logger.info(
            "%s %s %s model=%s client=%s status=%s",
            module,
            method,
            "kbin" if kencoded else "xml",
            model or "-",
            info.client_ip or "-",
            result.status,
        )
        if not result.content:
            result.content = {}

        response_attrs = {"status": str(result.status)}
        response_content = result.content
        if isinstance(response_content, list):
            response_nodes = []
            for node in response_content:
                node = dict(node)
                attrs = response_attrs.copy()
                attrs.update(node.pop("@attr", {}))
                node["@attr"] = attrs
                response_nodes.append(node)
            response_data = {"response": {result.root_name or module: response_nodes}}
        else:
            response_attrs.update(response_content.pop("@attr", {}))
            response_data = {
                "response": {
                    result.root_name or module: {
                        "@attr": response_attrs,
                        **response_content,
                    }
                }
            }
        encoding = result.encoding or parsed.encoding
        output = (
            kbin_encode(response_data, encoding, True)
            if parsed.kencoded
            else data_to_xml(response_data, encoding)
        )
        response_headers = {"X-Compress": "none"}
        should_compress = result.compress if result.compress is not None else compressed
        if should_compress and len(output) > 500:
            output = deflate(output)
            response_headers["X-Compress"] = "lz77"
        if result.encrypt if result.encrypt is not None else encrypted:
            key = KonmaiEncrypt()
            output = key.crypt(output)
            response_headers["X-Eamuse-Info"] = key.public_key
        return Response(
            output, media_type="application/octet-stream", headers=response_headers
        )

    @staticmethod
    def _find_call(call: dict) -> tuple[str, str]:
        for module, value in call.items():
            if module.startswith("@"):
                continue
            values = value if isinstance(value, list) else [value]
            methods = [
                item["@attr"]["method"]
                for item in values
                if isinstance(item, dict) and "method" in item.get("@attr", {})
            ]
            if methods:
                return module, ".".join(methods)
        raise ValueError("call does not contain a module method")


def build_konami_app(cfg) -> Starlette:
    """Build a standalone e-amusement app with Artemis route sets."""
    from server.konami.services import ArtemisServices
    from server.konami.titles.popn import PopnRoutes

    popn = PopnRoutes(cfg)
    services = ArtemisServices(cfg, popn.game_codes)
    servlet = KonamiServlet((services.register, popn.register))
    return Starlette(debug=cfg.server.is_develop, routes=servlet.get_routes())
