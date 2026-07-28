"""Starlette application adapter for the Konami service."""

from __future__ import annotations

import logging
import struct
from typing import Iterable

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.applications import Starlette

from .encryption import KonmaiEncrypt
from .kbin import decode as kbin_decode, encode as kbin_encode, is_kbin
from .lzkn import deflate, inflate
from .protocol import EamuseBody, EamuseInfo, EamuseResponse
from .router import EamuseRouter, KonamiPlugin
from .xml import data_to_xml, xml_to_data


class KonamiServlet:
    def __init__(self, plugins: Iterable[KonamiPlugin] = ()) -> None:
        self.logger = logging.getLogger("konami")
        self.router = EamuseRouter()
        self.plugins = tuple(plugins)
        for plugin in self.plugins:
            plugin.register(self.router)

    def get_routes(self) -> list[Route]:
        # Konami clients commonly post to /, while services discovered through
        # services.get may use arbitrary module paths.  The catch-all route is
        # therefore intentional.
        return [Route("/{path:path}", self.handle, methods=["POST"])]

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
                data = xml_to_data(body)
                request_encoding = "utf-8"
                kencoded = False
            call = data.get("call", {})
            module, method = self._find_call(call)
            model = call.get("@attr", {}).get("model", "")
            game_code = model.split(":", 1)[0]
        except (ValueError, UnicodeDecodeError, IndexError, struct.error) as exc:
            self.logger.warning("Unable to decode e-amusement request: %s", exc)
            return Response(status_code=404)

        info = EamuseInfo(
            game_code=game_code,
            module=module,
            method=method,
            model=model,
            client_ip=request.client.host if request.client else "",
            host=request.headers.get(
                "x-forwarded-host", request.headers.get("host", "")
            ),
            protocol=request.headers.get("x-forwarded-proto", request.url.scheme),
            proxy=bool(request.headers.get("x-forwarded-host")),
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
            for item in values:
                if isinstance(item, dict) and "method" in item.get("@attr", {}):
                    return module, item["@attr"]["method"]
        raise ValueError("call does not contain a module method")


def build_konami_app(cfg) -> Starlette:
    """Build a standalone Konami app using the same plugins as the shared app."""
    from core.konami.core_plugin import CoreKonamiPlugin
    from konami.titles.popn import PopnPlugin

    popn = PopnPlugin(cfg)
    servlet = KonamiServlet((CoreKonamiPlugin(cfg, popn.game_codes), popn))
    return Starlette(debug=cfg.server.is_develop, routes=servlet.get_routes())
