"""Starlette application adapter for the Konami service."""

from __future__ import annotations

import logging
import struct
from collections.abc import Callable, Iterable
from urllib.parse import parse_qs
from xml.etree.ElementTree import ParseError

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from .encryption import KonmaiEncrypt
from .kbin import decode as kbin_decode
from .kbin import encode as kbin_encode
from .kbin import is_kbin
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
            # Older EA3 configurations advertise the service mounted at
            # /core/keepalive.  Keep both forms valid for migrated cabinets.
            Route("/core/keepalive", self.keepalive, methods=["GET"]),
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
        eamuse_info = request.headers.get("x-eamuse-info")
        encrypted = bool(eamuse_info)
        try:
            if encrypted:
                body = KonmaiEncrypt(eamuse_info).crypt(body)

            compressed = request.headers.get("x-compress", "none") == "lz77"
            if compressed:
                body = inflate(body)
        except (ValueError, UnicodeDecodeError, IndexError, struct.error) as exc:
            # The legacy middleware treats transport failures as an invalid
            # request, rather than allowing malformed headers/ciphertext to
            # escape as an HTTP 500.
            self.logger.warning("Unable to decode e-amusement transport: %s", exc)
            return Response(status_code=404)

        try:
            if is_kbin(body):
                data, request_encoding = kbin_decode(body)
                kencoded = True
            else:
                request_encoding = detect_xml_encoding(body)
                data = xml_to_data(body, request_encoding)
                kencoded = False
            call = data.get("call", {})
            try:
                module, method = self._find_call(call)
            except ValueError:
                # EA3 can disable URL-slash routing and put model/module/
                # method in the query string while still posting the encoded
                # call body to `/`.  Accept that legacy layout as well.
                model, module, method = self._query_call_metadata(request.url.query)
                if not module or not method:
                    raise
            model = call.get("@attr", {}).get(
                "model", request.query_params.get("model", "")
            )
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

        forwarded_host = _forwarded_header(request.headers.get("x-forwarded-host"))
        forwarded_proto = _forwarded_header(request.headers.get("x-forwarded-proto"))
        forwarded_port = _forwarded_header(request.headers.get("x-forwarded-port"))
        forwarded_for = _forwarded_header(request.headers.get("x-forwarded-for"))
        advertised_host = forwarded_host or request.headers.get("host", "")
        if (
            forwarded_host
            and forwarded_port
            and not _has_port(forwarded_host)
            and not (forwarded_port == "80" and forwarded_proto == "http")
            and not (forwarded_port == "443" and forwarded_proto == "https")
        ):
            advertised_host = f"{forwarded_host}:{forwarded_port}"
        client_ip = forwarded_for or (request.client.host if request.client else "")
        if ":" in client_ip:
            client_ip = "127.0.0.1"
        info = EamuseInfo(
            game_code=game_code,
            module=module,
            method=method,
            model=model,
            client_ip=client_ip,
            host=advertised_host,
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
        try:
            matched = await self.router.dispatch(parsed, info, result)
        except Exception:
            # EA3 expects a protocol response even when a title handler fails.
            # Returning status 1 matches the legacy middleware contract and
            # lets the cabinet report/retry the failed call instead of seeing
            # an HTML/HTTP 500 response.
            self.logger.exception("Konami handler failed for %s.%s", module, method)
            matched = True
            result.status = 1
            result.content = {}
        self.logger.info(
            "%s %s %s path=%s model=%s client=%s route=%s status=%s",
            module,
            method,
            "kbin" if kencoded else "xml",
            request.url.path,
            model or "-",
            info.client_ip or "-",
            "matched" if matched else "unmatched",
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
            # EA3 negotiates a fresh response key.  The client uses the
            # returned X-Eamuse-Info header to decrypt this response; reusing
            # the request key leaves Pop'n reporting a network error after
            # services.get even though the HTTP exchange succeeded.
            key = KonmaiEncrypt()
            output = key.crypt(output)
            response_headers["X-Eamuse-Info"] = key.public_key
        self.logger.info(
            "%s %s response_bytes=%s response_compress=%s response_encrypt=%s",
            module,
            method,
            len(output),
            response_headers["X-Compress"],
            "X-Eamuse-Info" in response_headers,
        )
        return Response(
            output, media_type="application/octet-stream", headers=response_headers
        )

    @staticmethod
    def _find_call(call: dict) -> tuple[str, str]:
        """Find the concrete XRPC module in direct or EA3-wrapped calls.

        Most clients send ``<call><pcb method="boot">`` directly.  EA3 also
        permits the service alias registered by a module (for example
        ``local3 -> pcb``) to wrap that call.  The DLL inspected for Pop'n Hi
        Cheers registers both forms, so accept either wire layout.
        """
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
            for item in values:
                if not isinstance(item, dict):
                    continue
                nested = {
                    key: nested_value
                    for key, nested_value in item.items()
                    if not key.startswith("@")
                }
                if nested:
                    return KonamiServlet._find_call(nested)
        raise ValueError("call does not contain a module method")

    @staticmethod
    def _query_call_metadata(query: str) -> tuple[str, str, str]:
        values = parse_qs(query.lstrip("?"), keep_blank_values=True)
        model = values.get("model", [""])[0]
        module = values.get("module", [""])[0]
        method = values.get("method", [""])[0]
        if "." in method and not module:
            module, method = method.split(".", 1)
        return model, module, method



def build_konami_app(cfg) -> Starlette:
    """Build a standalone e-amusement app with Artemis route sets."""
    servlet = build_konami_servlet(cfg)
    return Starlette(debug=cfg.server.is_develop, routes=servlet.get_routes())


def build_konami_servlet(cfg) -> KonamiServlet:
    """Build the shared Konami servlet used by every deployment mode."""
    from server.konami.services import ArtemisServices
    from server.konami.titles.ddr import DDRRoutes
    from server.konami.titles.iidx import IIDXRoutes
    from server.konami.titles.jubeat import JubeatRoutes
    from server.konami.titles.museca import MusecaRoutes
    from server.konami.titles.popn import PopnRoutes
    from server.konami.titles.sdvx import SDVXRoutes

    popn = PopnRoutes(cfg)
    ddr = DDRRoutes(cfg)
    iidx = IIDXRoutes(cfg)
    jubeat = JubeatRoutes(cfg)
    museca = MusecaRoutes(cfg)
    sdvx = SDVXRoutes(cfg)
    game_codes = (
        popn.game_codes
        + ddr.game_codes
        + iidx.game_codes
        + jubeat.game_codes
        + museca.game_codes
        + sdvx.game_codes
    )

    def service_modules(game_code: str, model: str):
        if game_code in ddr.game_codes:
            return ddr.service_modules(game_code, model)
        if game_code in iidx.game_codes:
            return iidx.service_modules(game_code, model)
        if game_code in jubeat.game_codes:
            return jubeat.service_modules(game_code, model)
        if game_code in sdvx.game_codes:
            return sdvx.service_modules(game_code, model)
        if game_code in museca.game_codes:
            return museca.service_modules(game_code, model)
        return popn.service_modules(game_code, model)

    services = ArtemisServices(cfg, game_codes, service_modules)
    return KonamiServlet(
        (
            services.register,
            popn.register,
            ddr.register,
            iidx.register,
            jubeat.register,
            sdvx.register,
            museca.register,
        )
    )


def _forwarded_header(value: str | None) -> str:
    """Use the first value from a proxy header, matching common proxy syntax."""
    return value.split(",", 1)[0].strip() if value else ""


def _has_port(host: str) -> bool:
    if host.startswith("["):
        return "]:" in host
    return host.count(":") == 1
