from starlette.applications import Starlette

from server.konami.app import KonamiServlet, _forwarded_header, _has_port
from server.konami.encryption import KonmaiEncrypt
from server.konami.kbin import decode as kbin_decode
from server.konami.kbin import encode as kbin_encode
from server.konami.lzkn import deflate, deflate_dummy, inflate
from server.konami.titles.popn.hicheers import PopnRepository, PopnRoutes
from server.konami.xml import data_to_xml, detect_xml_encoding, xml_to_data


def test_kbin_binary_round_trip():
    payload = {
        "response": {
            "playerdata": {
                "town": {"@attr": {"__type": "bin"}, "@content": bytes(range(8))}
            }
        }
    }
    decoded, _ = kbin_decode(kbin_encode(payload, "utf-8", True))
    assert decoded["response"]["playerdata"]["town"]["@content"] == bytes(range(8))


def test_transport_codecs_round_trip():
    payloads = [b"", b"hello", b"a small payload for konami", bytes(range(256)) * 8]
    for payload in payloads:
        assert inflate(deflate_dummy(payload)) == payload
        assert inflate(deflate(payload)) == payload

    key = KonmaiEncrypt("1-01020304-0506")
    assert KonmaiEncrypt(key.public_key).crypt(key.crypt(b"hello")) == b"hello"


def test_kbin_typed_nodes_with_attributes_round_trip():
    payload = {
        "response": {
            "facility": {
                "@attr": {"expire": "86400", "status": "0"},
                "location": {
                    "id": {"@attr": {"__type": "str"}, "@content": "ea"},
                    "latitude": {"@attr": {"__type": "s32"}, "@content": [6666]},
                },
                "portfw": {
                    "globalip": {
                        "@attr": {"__type": "ip4"},
                        "@content": [0x01020304],
                    }
                },
            }
        }
    }
    decoded, _ = kbin_decode(kbin_encode(payload, "utf-8", True))
    facility = decoded["response"]["facility"]
    assert facility["@attr"]["expire"] == "86400"
    assert facility["@attr"]["status"] == "0"
    assert facility["location"]["latitude"]["@content"] == [6666]
    assert facility["portfw"]["globalip"]["@content"] == [0x01020304]


def test_kbin_scalar_numeric_lanes_match_avs_layout():
    payload = {
        "response": {
            "facility": {
                "byte_a": {"@attr": {"__type": "u8"}, "@content": [1]},
                "text": {"@attr": {"__type": "str"}, "@content": "ok"},
                "word": {"@attr": {"__type": "u16"}, "@content": [0x1234]},
                "byte_b": {"@attr": {"__type": "u8"}, "@content": [2]},
            }
        }
    }
    encoded = kbin_encode(payload, "utf-8", True)
    node_length = int.from_bytes(encoded[4:8], "big")
    data = encoded[12 + node_length :]
    assert data == bytes.fromhex("01020000000000036f6b000012340000")


def test_xml_shift_jis_round_trip():
    payload = {"call": {"playerdata": {"@attr": {"name": "ポップン"}}}}
    encoded = data_to_xml(payload, "shift_jis")
    assert detect_xml_encoding(encoded) == "shift_jis"
    assert xml_to_data(encoded)["call"]["playerdata"]["@attr"]["name"] == "ポップン"


def test_dotted_method_detection():
    assert KonamiServlet._find_call(
        {"posevent": [{"@attr": {"method": "income"}}, {"@attr": {"method": "sales"}}]}
    ) == ("posevent", "income.sales")


def test_query_string_call_metadata_is_supported():
    assert KonamiServlet._query_call_metadata(
        "?model=M39:J:D:A:2026041500&module=services&method=get"
    ) == ("M39:J:D:A:2026041500", "services", "get")


def test_unknown_title_calls_are_not_silently_acknowledged():
    import asyncio

    from server.konami.protocol import EamuseBody, EamuseInfo, EamuseResponse
    from server.konami.router import EamuseRouter

    router = EamuseRouter()
    body = EamuseBody(
        data={"call": {"game": {"@attr": {"method": "missing"}}}},
        raw=b"", module="game", method="missing", model="M39:J:D:A:2026041500"
    )
    response = EamuseResponse(root_name="game")
    matched = asyncio.run(
        router.dispatch(
            body,
            EamuseInfo("M39", "game", "missing", "M39:J:D:A:2026041500"),
            response,
        )
    )
    assert matched is False
    assert response.status == 1


def test_popn_modules_are_advertised_for_m39():
    modules = PopnRoutes.service_modules("M39", "M39:J:D:A:2026041500")
    assert modules == ("local2", "lobby2")
    assert "JMP" not in PopnRoutes.game_codes


def test_popn_m39_runtime_route_aliases_are_registered():
    from server.konami.router import EamuseRouter

    routes = PopnRoutes.__new__(PopnRoutes)
    router = EamuseRouter()
    routes.register(router)
    assert {
        "player24.buy", "player24.read_score",
        "player.read", "player.new", "player.write",
        "info24.common", "lobby24.getList",
        "info.common", "pcb.boot", "loctest24.log",
    } <= set(
        router._routes["M39"]
    )
    assert not {
        "player.shop_buy", "game.e", "game.s",
    } & set(router._routes["M39"])
    assert not hasattr(router, "_fallback")


def test_popn_m39_player_boot_payload_round_trip_shape():
    import asyncio

    from server.konami.protocol import EamuseInfo, EamuseResponse
    from server.konami.titles.popn.hicheers import SPECS, PopnVersionHandler

    class Repo:
        async def profile(self, refid):
            return {"name": "PLAYER", "friendId": "000000000001"}

        async def save_profile(self, refid, profile):
            return None

        async def rivals(self, refid):
            return {"rivals": []}

        async def scores(self, refid, version, force_version=False):
            return {"scores": {}}

        async def params(self, refid, version):
            return {"params": {}}

        async def achievements(self, refid, version, default):
            return default

    handler = PopnVersionHandler(Repo(), SPECS["v27"])
    info = EamuseInfo(
        game_code="M39", module="player", method="new", model="M39:J:D:A:2026041500"
    )
    response = EamuseResponse(root_name="player")
    asyncio.run(handler.new(info, {"@attr": {"ref_id": "REFID", "name": "PLAYER"}}, response))
    assert response.status == 0
    assert response.content["account"]["name"]["@attr"]["__type"] == "str"
    assert response.content["music"] == []


def test_popn_only_exposes_hi_cheers():
    from server.konami.router import EamuseRouter
    from server.konami.titles.popn.hicheers import PopnRoutes

    routes = PopnRoutes.__new__(PopnRoutes)
    router = EamuseRouter()
    routes.register(router)
    assert PopnRoutes.game_codes == ("M39",)
    assert {"player.read", "player.write", "player24.read"} <= set(router._routes["M39"])


def test_services_response_includes_popn_modules():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse
    from server.konami.services import ArtemisServices

    services = ArtemisServices.__new__(ArtemisServices)
    services.module_provider = PopnRoutes.service_modules
    services.data = SimpleNamespace(
        config=SimpleNamespace(
            konami=SimpleNamespace(
                hostname="localhost", port=5730, ping_ip="127.0.0.1"
            )
        )
    )
    response = EamuseResponse(root_name="services")
    info = EamuseInfo(
        game_code="M39",
        module="services",
        method="get",
        model="M39:J:D:A:2026041500",
        host="cabinet.example",
        protocol="http",
    )

    asyncio.run(services.services_get(info, {}, response))
    names = {item["@attr"]["name"] for item in response.content["item"]}
    assert {"keepalive", "local2", "local3", "lobby2"} <= names
    assert "player24" not in names
    assert response.content["item"][0]["@attr"]["name"] == "cardmng"
    assert response.content["item"][-2]["@attr"]["name"] == "ntp"
    assert response.content["item"][-1]["@attr"]["name"] == "keepalive"
    keepalive = next(
        item for item in response.content["item"] if item["@attr"]["name"] == "keepalive"
    )
    assert keepalive["@attr"]["url"].startswith("http://127.0.0.1/core/keepalive?")


def test_facility_response_uses_bemaniutils_defaults():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse
    from server.konami.services import ArtemisServices

    services = ArtemisServices.__new__(ArtemisServices)
    services.data = SimpleNamespace(
        config=SimpleNamespace(
            konami=SimpleNamespace(hostname="localhost", matching_port=5730)
        )
    )
    response = EamuseResponse(root_name="facility")
    info = EamuseInfo(
        game_code="M39", module="facility", method="get", model="M39:J:D:A:2026041500"
    )

    asyncio.run(services.facility_get(info, {}, response))
    facility = response.content
    assert facility["public"]["name"]["@content"] == "."
    assert facility["share"]["eacoin"]["notchamount"]["@content"] == [3000]
    assert facility["share"]["eacoin"]["notchcount"]["@content"] == [3]
    assert facility["share"]["eacoin"]["supplylimit"]["@content"] == [10000]
    assert facility["share"]["eapass"]["valid"]["@content"] == [365]


def test_services_remote_client_does_not_receive_loopback_keepalive():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse
    from server.konami.services import ArtemisServices

    services = ArtemisServices.__new__(ArtemisServices)
    services.module_provider = PopnRoutes.service_modules
    services.data = SimpleNamespace(
        config=SimpleNamespace(
            konami=SimpleNamespace(
                hostname="eamuse.example", port=5730, ping_ip="127.0.0.1"
            )
        )
    )
    response = EamuseResponse(root_name="services")
    info = EamuseInfo(
        game_code="M39", module="services", method="get",
        model="M39:J:D:A:2026041500", host="eamuse.example:5730",
        client_ip="96.233.42.212", protocol="http",
    )
    asyncio.run(services.services_get(info, {}, response))
    keepalive = next(
        item for item in response.content["item"] if item["@attr"]["name"] == "keepalive"
    )
    assert keepalive["@attr"]["url"].startswith("http://eamuse.example:5730/core/keepalive?")
    assert "127.0.0.1" not in keepalive["@attr"]["url"]


def test_core_service_routes_match_bemaniutils_core_surface():
    from server.konami.router import EamuseRouter
    from server.konami.services import ArtemisServices

    services = ArtemisServices.__new__(ArtemisServices)
    router = EamuseRouter()
    services.game_codes = ("M39",)
    services.register(router)
    assert {
        "services.get",
        "facility.get",
        "lobby.get",
        "lobby.getlist",
        "local.get",
        "local3.get",
        "message.get",
        "package.list",
        "pcbevent.put",
        "dlstatus.progress",
        "pcbtracker.alive",
        "pkglist.nr_entry",
        "posevent.income",
        "eacoin.checkout",
        "eacoin.checkin",
        "eacoin.consume",
        "eacoin.getlog",
        "eacoin.opcheckin",
        "eacoin.opcheckout",
        "eacoin.opchpass",
        "cardmng.inquire",
        "cardmng.getrefid",
        "cardmng.getdatalist",
        "cardmng.getkeepspan",
        "cardmng.authpass",
        "cardmng.bindmodel",
    } <= set(router._routes["M39"])
    assert not {
        "eventlog.write",
        "tax.get_phase",
        "pcb.boot",
        "sidmgr.open",
    } & set(router._routes["M39"])


def test_popn_legacy_profile_migration_prefers_title_namespace():
    calls = []

    class Konami:
        async def get_profile(self, refid):
            return None

        async def get_document(self, refid, game, collection, version=""):
            calls.append((refid, game, collection, version))
            return {"name": "legacy"} if game == "K39" else None

        async def put_profile(self, refid, profile):
            calls.append(("put_profile", refid))

    repository = PopnRepository.__new__(PopnRepository)
    repository.data = type("Data", (), {"konami": Konami()})()
    repository.game_code = "K39"
    repository.profile_code = "M39"
    import asyncio

    assert asyncio.run(repository.profile("REFID"))["name"] == "legacy"
    assert calls[0] == ("REFID", "K39", "profile", "")


def test_popn_profiles_get_stable_nonzero_friend_ids():
    class Konami:
        async def get_profile(self, refid):
            return None

        async def get_document(self, *args):
            return None

    repository = PopnRepository.__new__(PopnRepository)
    repository.data = type("Data", (), {"konami": Konami()})()
    repository.game_code = "M39"
    repository.profile_code = "M39"
    import asyncio

    first = asyncio.run(repository.profile("REFID"))
    second = asyncio.run(repository.profile("OTHER"))
    assert len(first["friendId"]) == 12
    assert first["friendId"] != "000000000000"
    assert first["friendId"] != second["friendId"]


def test_popn_rival_accepts_normalized_profile():
    class Konami:
        async def get_profile(self, refid):
            return {"name": "normalized"} if refid == "RIVAL" else None

        async def put_rivals(self, refid, rival_ids):
            return None

    repository = PopnRepository.__new__(PopnRepository)
    repository.data = type("Data", (), {"konami": Konami()})()
    repository.game_code = "K39"
    repository.profile_code = "M39"
    async def rivals(refid):
        return {"rivals": []}

    repository.rivals = rivals
    import asyncio

    assert asyncio.run(repository.add_rival("OWNER", "RIVAL")) is True


def test_score_sharing_setting_controls_version_reads():
    class Konami:
        async def get_scores(self, refid, version):
            return {"scores": {version: {"score": 1, "cnt": 1, "clear_type": 1}}}

        async def get_document(self, *args):
            return None

    class Config:
        class KonamiConfig:
            enable_score_sharing = False

        konami = KonamiConfig()

    repository = PopnRepository.__new__(PopnRepository)
    repository.data = type("Data", (), {"konami": Konami(), "config": Config()})()
    repository.game_code = "M39"
    repository.profile_code = "M39"
    import asyncio

    result = asyncio.run(repository.scores("REFID", "v21"))
    assert list(result["scores"]) == ["v21"]


def test_forwarded_headers_use_first_value():
    assert _forwarded_header("public.example:443, proxy.local:5730") == "public.example:443"
    assert _has_port("public.example:443")
    assert not _has_port("public.example")


def test_friend_id_generation_is_stable_and_nonzero():
    from server.konami.services import _friend_id

    assert _friend_id("REFID") == _friend_id("REFID")
    assert len(_friend_id("REFID")) == 12
    assert _friend_id("REFID") != "000000000000"


def test_handler_failure_returns_protocol_status_one():
    def register(router):
        async def broken(info, data, response):
            raise RuntimeError("expected test failure")

        router.add("M39", "game", "get", broken)

    servlet = KonamiServlet((register,))
    app = Starlette(routes=servlet.get_routes())
    payload = {
        "call": {
            "@attr": {"model": "M39:J:D:A:2026041500"},
            "game": {"@attr": {"method": "get"}},
        }
    }
    body = kbin_encode(payload, "utf-8", True)

    async def run():
        messages = [{"type": "http.request", "body": body, "more_body": False}]
        sent = []

        async def receive():
            return messages.pop(0)

        async def send(message):
            sent.append(message)

        await app(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/",
                "raw_path": b"/",
                "query_string": b"",
                "headers": [(b"host", b"127.0.0.1:5730")],
                "client": ("127.0.0.1", 1),
                "server": ("127.0.0.1", 5730),
                "root_path": "",
            },
            receive,
            send,
        )
        return sent

    import asyncio

    sent = asyncio.run(run())
    output = b"".join(
        message.get("body", b"")
        for message in sent
        if message["type"] == "http.response.body"
    )
    decoded, _ = kbin_decode(output)
    assert decoded["response"]["game"]["@attr"]["status"] == "1"


def test_malformed_transport_returns_404():
    servlet = KonamiServlet()
    app = Starlette(routes=servlet.get_routes())

    async def run():
        sent = []

        async def receive():
            return {"type": "http.request", "body": b"invalid", "more_body": False}

        async def send(message):
            sent.append(message)

        await app(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/",
                "raw_path": b"/",
                "query_string": b"",
                "headers": [(b"host", b"127.0.0.1:5730"), (b"x-eamuse-info", b"bad")],
                "client": ("127.0.0.1", 1),
                "server": ("127.0.0.1", 5730),
                "root_path": "",
            },
            receive,
            send,
        )
        return sent

    import asyncio

    sent = asyncio.run(run())
    assert sent[0]["status"] == 404


def test_card_bindmodel_persists_game_binding():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse
    from server.konami.services import ArtemisServices

    calls = []

    class Konami:
        async def get_profile(self, refid):
            return {"name": "player"}

        async def get_document(self, *args):
            raise AssertionError("normalized profile should be preferred")

        async def put_profile(self, *args):
            calls.append(("profile", args))

        @staticmethod
        def _stable_id(value):
            return 12345678

        async def put_extid(self, *args):
            calls.append(("extid", args))

    services = ArtemisServices.__new__(ArtemisServices)
    services.data = SimpleNamespace(konami=Konami())
    info = EamuseInfo(
        game_code="M39", module="cardmng", method="bindmodel", model="M39"
    )
    response = EamuseResponse(root_name="cardmng")

    asyncio.run(
        services.card_bindmodel(
            info, {"@attr": {"refid": "REFID"}}, response
        )
    )
    assert calls == [("extid", ("REFID", "M39", 12345678))]
    assert response.content["@attr"]["dataid"] == "REFID"


def test_card_profile_migrates_shared_popn_namespace():
    import asyncio
    from types import SimpleNamespace

    from server.konami.services import ArtemisServices

    calls = []

    class Konami:
        async def get_profile(self, refid):
            return None

        async def get_document(self, refid, game, collection):
            return {"name": "shared"} if game == "M39" else None

        async def put_profile(self, *args):
            calls.append(args)

    services = ArtemisServices.__new__(ArtemisServices)
    services.data = SimpleNamespace(konami=Konami())
    profile = asyncio.run(services._card_profile("REFID", "K39"))
    assert profile == {"name": "shared"}
    assert calls == [("REFID", {"name": "shared"})]


def test_card_inquire_reports_real_game_binding():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse
    from server.konami.services import ArtemisServices

    class Konami:
        async def get_profile(self, refid):
            return {"pin": "1234"}

        async def get_document(self, *args):
            raise AssertionError("normalized profile should be preferred")

        async def get_extid(self, refid, game):
            return None

    services = ArtemisServices.__new__(ArtemisServices)
    services.data = SimpleNamespace(konami=Konami())
    info = EamuseInfo(
        game_code="M39", module="cardmng", method="inquire", model="M39"
    )
    response = EamuseResponse(root_name="cardmng")
    asyncio.run(
        services.card_inquire(
            info, {"@attr": {"cardid": "0123456789ABCDEF"}}, response
        )
    )
    assert response.content["@attr"]["binded"] == "0"


def test_core_discovery_chain_survives_encrypted_kbin_transport():
    """Exercise the deployed servlet boundary, including decrypt/decompress."""
    import asyncio
    from types import SimpleNamespace

    from server.konami.services import ArtemisServices

    cfg = SimpleNamespace(
        server=SimpleNamespace(is_develop=True),
        konami=SimpleNamespace(
            hostname="konami.example",
            port=5730,
            ping_ip="192.0.2.10",
            matching_port=5730,
            maintenance_mode=False,
            maintenance_message="",
            tax_phase=0,
            enable_paseli=False,
        ),
    )
    services = ArtemisServices.__new__(ArtemisServices)
    services.data = SimpleNamespace(config=cfg)
    services.game_codes = ("M39",)
    services.module_provider = PopnRoutes.service_modules

    from server.konami.app import KonamiServlet

    servlet = KonamiServlet((services.register,))
    key = "1-01020304-0506"

    async def request(module, method):
        request_data = {
            "call": {
                "@attr": {
                    "model": "M39:J:D:A:2026041500",
                    "srcid": "PCB123456",
                },
                module: {"@attr": {"method": method}},
            }
        }
        plain = kbin_encode(request_data, "utf-8", True)
        wire = KonmaiEncrypt(key).crypt(deflate(plain))
        response = await _asgi_response(servlet, module, wire, key)
        response_key = response["headers"]["x-eamuse-info"]
        assert response_key == key
        body = KonmaiEncrypt(response_key).crypt(response["body"])
        if response["headers"].get("x-compress") == "lz77":
            body = inflate(body)
        decoded, _ = kbin_decode(body)
        return response, decoded

    async def run():
        results = {}
        for module, method in (
            ("services", "get"),
            ("facility", "get"),
            ("message", "get"),
            ("package", "list"),
            ("pcbtracker", "alive"),
        ):
            results[module] = await request(module, method)
        return results

    # The small ASGI adapter below is intentionally local to the test so this
    # protocol fixture does not add a production dependency on TestClient.
    async def _asgi_response(servlet, module, wire, eamuse_info):
        messages = [{"type": "http.request", "body": wire, "more_body": False}]
        sent = []

        async def receive():
            return messages.pop(0)

        async def send(message):
            sent.append(message)

        app = Starlette(routes=servlet.get_routes())
        await app(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/" + module,
                "raw_path": ("/" + module).encode(),
                "query_string": b"",
                "headers": [
                    (b"host", b"cabinet.example:5730"),
                    (b"x-eamuse-info", eamuse_info.encode()),
                    (b"x-compress", b"lz77"),
                    (b"x-forwarded-proto", b"https"),
                    (b"x-forwarded-host", b"public.example"),
                    (b"x-forwarded-for", b"203.0.113.7"),
                ],
                "client": ("127.0.0.1", 1),
                "server": ("127.0.0.1", 5730),
                "root_path": "",
            },
            receive,
            send,
        )
        headers = dict(sent[0]["headers"])
        return {
            "status": sent[0]["status"],
            "headers": {key.decode(): value.decode() for key, value in headers.items()},
            "body": b"".join(
                message.get("body", b"")
                for message in sent
                if message["type"] == "http.response.body"
            ),
        }

    results = asyncio.run(run())
    assert all(result[0]["status"] == 200 for result in results.values())
    assert all(
        result[1]["response"][module]["@attr"]["status"] == "0"
        for module, result in results.items()
    )
    assert results["services"][1]["response"]["@attr"]["dstid"] == "PCB123456"
    service_items = results["services"][1]["response"]["services"]["item"]
    assert any(item["@attr"]["name"] == "local2" for item in service_items)
    assert any(item["@attr"]["name"] == "lobby2" for item in service_items)
    local_service = next(item for item in service_items if item["@attr"]["name"] == "local2")
    assert local_service["@attr"]["url"] == "https://public.example/"
    keepalive_service = next(item for item in service_items if item["@attr"]["name"] == "keepalive")
    assert keepalive_service["@attr"]["url"].startswith("https://192.0.2.10/core/keepalive?")
