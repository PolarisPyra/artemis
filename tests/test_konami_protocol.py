from starlette.applications import Starlette

from server.konami.app import KonamiServlet, _forwarded_header, _has_port
from server.konami.encryption import KonmaiEncrypt
from server.konami.kbin import decode as kbin_decode
from server.konami.kbin import encode as kbin_encode
from server.konami.lzkn import deflate, deflate_dummy, inflate
from server.konami.titles.ddr import DDRRoutes
from server.konami.titles.iidx import IIDXRoutes
from server.konami.titles.jubeat import JubeatRoutes
from server.konami.titles.museca import MusecaRoutes
from server.konami.titles.popn import PopnRepository, PopnRoutes
from server.konami.titles.sdvx import SDVXRoutes
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
        "player.shop_buy", "player.read_option", "game.e", "game.s",
        "game.active", "pcb24.boot", "lobby24.getList",
    } <= set(
        router._routes["M39"]
    )
    assert not hasattr(router, "_fallback")


def test_popn_m39_player_boot_payload_round_trip_shape():
    import asyncio

    from server.konami.protocol import EamuseInfo, EamuseResponse
    from server.konami.titles.popn import SPECS, PopnVersionHandler

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

    handler = PopnVersionHandler(Repo(), SPECS["v21"])
    info = EamuseInfo(
        game_code="M39", module="player", method="new", model="M39:J:D:A:2026041500"
    )
    response = EamuseResponse(root_name="player")
    asyncio.run(handler.new(info, {"@attr": {"ref_id": "REFID", "name": "PLAYER"}}, response))
    assert response.status == 0
    assert response.content["base"]["name"]["@attr"]["__type"] == "str"
    assert response.content["hiscore"]["@attr"]["__type"] == "bin"


def test_iidx_route_surface_covers_supported_asphyxia_modules():
    from server.konami.router import EamuseRouter

    routes = IIDXRoutes.__new__(IIDXRoutes)
    router = EamuseRouter()
    routes.register(router)
    registered = router._routes["LDJ"]
    assert {
        "pc.common",
        "pc.reg",
        "pc.get",
        "pc.getname",
        "pc.save",
        "shop.getname",
        "music.reg",
        "grade.raised",
        "ranking.getranker",
        "gameSystem.systemInfo",
    } <= set(registered)
    assert "pc.common" in router._routes["LDJ"]
    assert any(name.startswith("IIDX21pc.") for name in router._routes["LDJ"])
    assert IIDXRoutes.game_codes == ("JDJ", "JDZ", "KDZ", "LDJ")


def test_iidx_common_payload_has_versioned_boot_fields():
    import asyncio

    from server.konami.protocol import EamuseInfo, EamuseResponse

    routes = IIDXRoutes.__new__(IIDXRoutes)
    response = EamuseResponse(root_name="pc")
    info = EamuseInfo(
        game_code="LDJ", module="IIDX22pc", method="common", model="LDJ:J:A:A:0"
    )
    asyncio.run(routes.pc_common(info, {}, response))
    assert response.content["limit"]["@attr"]["phase"] == "24"
    assert response.content["license"]["string"]["@attr"]["__type"] == "bin"
    assert IIDXRoutes.service_modules("LDJ") == ("local2",)

    info.module = "IIDX29pc"
    response = EamuseResponse(root_name="pc")
    asyncio.run(routes.pc_common(info, {}, response))
    assert "lane_gacha" in response.content
    assert response.content["world_tourism"]["@attr"]["open_list"] == "-1"


def test_iidx_profile_save_and_music_rank_round_trip():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse

    class Store:
        def __init__(self):
            self.profile = {"id": 1234, "idstr": "0000-1234", "name": "TEST"}
            self.documents = {}

        async def get_profile(self, refid):
            return self.profile

        async def put_profile(self, refid, value):
            self.profile = value

        async def get_document(self, refid, game, collection, version=""):
            return self.documents.get((refid, game, collection, version))

        async def put_document(self, refid, game, collection, value, version=""):
            self.documents[(refid, game, collection, version)] = value

    routes = IIDXRoutes.__new__(IIDXRoutes)
    store = Store()
    routes.data = SimpleNamespace(konami=store)
    info = EamuseInfo(game_code="LDJ", module="pc", method="save", model="LDJ:J:A:A:0")
    save = EamuseResponse(root_name="pc")
    asyncio.run(routes.pc_save(info, {"@attr": {"rid": "CARD"}, "name": {"@content": ["NEW"]}}, save))
    assert save.status == 0
    assert store.profile["name"] == "NEW"

    music = EamuseResponse(root_name="music")
    asyncio.run(
        routes.music_reg(
            info,
            {
                "@attr": {"rid": "CARD"},
                "m": {"@attr": {"mid": "42"}, "score": {"@content": [1234]}, "clear": {"@content": [5]}},
            },
            music,
        )
    )
    rank = EamuseResponse(root_name="music")
    asyncio.run(routes.music_getrank(info, {"@attr": {"rid": "CARD"}}, rank))
    assert rank.content["m"][0]["@content"][:2] == [-1, 42]


def test_jubeat_route_surface_covers_supported_asphyxia_modules():
    from server.konami.router import EamuseRouter

    routes = JubeatRoutes.__new__(JubeatRoutes)
    router = EamuseRouter()
    routes.register(router)
    registered = router._routes["L44"]
    assert {
        "gametop.regist",
        "gametop.get_info",
        "gametop.get_pdata",
        "gametop.get_mdata",
        "gametop.get_meeting",
        "gameend.regist",
        "shopinfo.regist",
        "lobby.entry",
        "netlog.send",
        "logger.report",
    } <= set(registered)
    assert JubeatRoutes.game_codes == ("H44", "I44", "J44", "K44", "L44")
    assert JubeatRoutes.service_modules("L44") == ("netlog", "slocal")


def test_ddr_route_surface_covers_supported_playerdata_modules():
    from server.konami.router import EamuseRouter

    routes = DDRRoutes.__new__(DDRRoutes)
    router = EamuseRouter()
    routes.register(router)
    registered = router._routes["HDX"]
    assert {
        "playerdata.usergamedata_advanced",
        "playerdata.usergamedata_recv",
        "playerdata.usergamedata_send",
        "system.convcardnumber",
        "eventlog.write",
    } <= set(registered)
    assert DDRRoutes.service_modules("HDX") == ("local2",)


def test_ddr_opaque_usergamedata_records_round_trip():
    import asyncio
    import base64
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse

    class Store:
        def __init__(self):
            self.profile = {"collection": "profile"}

        async def get_profile(self, refid):
            return self.profile

        async def put_profile(self, refid, value):
            self.profile = value

    routes = DDRRoutes.__new__(DDRRoutes)
    store = Store()
    routes.data = SimpleNamespace(konami=store)
    info = EamuseInfo(game_code="HDX", module="playerdata", method="usergamedata_send", model="HDX:J:A:A:0")
    encoded = base64.b64encode(b"0,COMMON,a,b,").decode()
    sent = EamuseResponse(root_name="playerdata")
    asyncio.run(
        routes.usergamedata_send(
            info,
            {"data": {"refid": {"@content": ["REFID"]}, "record": {"d": [{"@content": [encoded]}]}}},
            sent,
        )
    )
    received = EamuseResponse(root_name="playerdata")
    asyncio.run(
        routes.usergamedata_recv(
            info,
            {"data": {"refid": {"@content": ["REFID"]}, "recv_csv": {"@content": ["COMMON,0"]}}},
            received,
        )
    )
    assert received.content["player"]["record_num"]["@content"] == [1]
    assert store.profile["usergamedata"]["COMMON"]["strdata"] == "a,b"


def test_sdvx_route_surface_covers_supported_game_modules():
    from server.konami.router import EamuseRouter

    routes = SDVXRoutes.__new__(SDVXRoutes)
    router = EamuseRouter()
    routes.register(router)
    registered = router._routes["KFC"]
    assert {
        "game.sv6_common",
        "game.sv6_new",
        "game.sv6_load",
        "game.sv6_save",
        "game.sv6_load_m",
        "game.sv6_save_m",
        "game.sv6_hiscore",
        "eventlog.write",
        "package.list",
        "ins.netlog",
    } <= set(registered)
    assert SDVXRoutes.service_modules("KFC") == ("local2",)


def test_sdvx_profile_and_score_state_round_trip():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse

    class Store:
        def __init__(self):
            self.profile = {"sdvxId": 123, "name": "PLAYER"}
            self.documents = {}

        async def get_profile(self, refid):
            return self.profile

        async def put_profile(self, refid, value):
            self.profile = value

        async def get_document(self, refid, game, collection, version=""):
            return self.documents.get((refid, game, collection, version))

        async def put_document(self, refid, game, collection, value, version=""):
            self.documents[(refid, game, collection, version)] = value

    routes = SDVXRoutes.__new__(SDVXRoutes)
    store = Store()
    routes.data = SimpleNamespace(konami=store)
    info = EamuseInfo(game_code="KFC", module="game", method="sv6_save", model="KFC:J:A:A:0")
    saved = EamuseResponse(root_name="game")
    asyncio.run(
        routes.profile_save(
            info,
            {"@attr": {"refid": "REFID"}, "appeal_id": {"@content": [7]}},
            saved,
        )
    )
    assert saved.status == 0
    assert store.profile["appeal"] == 7

    score = EamuseResponse(root_name="game")
    asyncio.run(
        routes.score_save(
            info,
            {
                "@attr": {"refid": "REFID"},
                "track": [{
                    "music_id": {"@content": [42]}, "music_type": {"@content": [2]},
                    "score": {"@content": [987654]}, "clear_type": {"@content": [4]},
                }],
            },
            score,
        )
    )
    loaded = EamuseResponse(root_name="game")
    asyncio.run(routes.score_load(info, {"@attr": {"refid": "REFID"}}, loaded))
    assert loaded.content["music"]["info"][0]["param"]["@content"][:6] == [42, 2, 987654, 0, 4, 0]


def test_sdvx_feature_state_round_trip():
    import asyncio
    from types import SimpleNamespace

    from server.konami.protocol import EamuseInfo, EamuseResponse

    class Store:
        def __init__(self):
            self.profiles = {"REFID": {"sdvxId": 123, "name": "PLAYER"}}
            self.documents = {}

        async def get_profile(self, refid):
            return self.profiles.get(refid)

        async def put_profile(self, refid, value):
            self.profiles[refid] = value

        async def get_document(self, refid, game, collection, version=""):
            return self.documents.get((refid, game, collection, version))

        async def put_document(self, refid, game, collection, value, version=""):
            self.documents[(refid, game, collection, version)] = value

        async def documents(self, game, collection, version="", refid=""):
            if collection == "profile":
                return [(key, value) for key, value in self.profiles.items() if not refid or key == refid]
            return [
                (key[0], value) for key, value in self.documents.items()
                if key[1] == game and key[2] == collection and (not refid or key[0] == refid)
            ]

    routes = SDVXRoutes.__new__(SDVXRoutes)
    store = Store()
    routes.data = SimpleNamespace(konami=store)
    info = EamuseInfo(game_code="KFC", module="game", method="sv6_save_c", model="KFC:J:A:A:0")
    saved = EamuseResponse(root_name="game")
    asyncio.run(routes.course_save(info, {
        "@attr": {"refid": "REFID"},
        "course": [{"course_id": {"@content": [77]}, "score": {"@content": [900000]}}],
    }, saved))
    assert saved.status == 0
    assert store.documents[("REFID", "KFC", "courses", "")]["courses"]["77"]["score"] == 900000

    mixed = EamuseResponse(root_name="game")
    asyncio.run(routes.mix_save(info, {
        "@attr": {"ref_id": "REFID"},
        "automation": {"mix_name": {"@content": ["TEST MIX"]}, "mix_code": {"@content": ["MIX1"]}},
    }, mixed))
    assert mixed.content["automation"]["mix_code"]["@content"] == ["MIX1"]
    loaded = EamuseResponse(root_name="game")
    asyncio.run(routes.mix_load(info, {
        "@attr": {"ref_id": "REFID"},
        "automation": {"mix_code": {"@content": ["MIX1"]}},
    }, loaded))
    assert loaded.content["automation"]["mix_name"]["@content"] == ["TEST MIX"]


def test_museca_title_route_surface_matches_bemaniutils():
    from server.konami.router import EamuseRouter

    routes = MusecaRoutes.__new__(MusecaRoutes)
    router = EamuseRouter()
    routes.register(router)
    assert {"game_3.common", "game_3.hiscore", "game_3.new", "game_3.load_m", "game_3.play_e"} <= set(router._routes["PIX"])
    assert routes.game_codes == ("PIX",)


def test_popn_old_versions_use_the_popn_title_module():
    from server.konami.router import EamuseRouter
    from server.konami.titles.popn import PopnRoutes

    routes = PopnRoutes.__new__(PopnRoutes)
    router = EamuseRouter()
    routes.register(router)
    assert {"G15", "H16", "I17", "J39"} <= set(PopnRoutes.game_codes)
    assert {"game.get", "playerdata.get", "playerdata.set"} <= set(router._routes["J39"])


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
    assert {"keepalive", "local2", "lobby2"} <= names
    assert "player24" not in names
    assert response.content["item"][0]["@attr"]["name"] == "cardmng"
    assert response.content["item"][-2]["@attr"]["name"] == "ntp"
    assert response.content["item"][-1]["@attr"]["name"] == "keepalive"
    keepalive = next(
        item for item in response.content["item"] if item["@attr"]["name"] == "keepalive"
    )
    assert keepalive["@attr"]["url"].startswith("http://127.0.0.1/core/keepalive?")


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


def test_core_service_routes_cover_ea3_boot_methods():
    from server.konami.router import EamuseRouter
    from server.konami.services import ArtemisServices

    services = ArtemisServices.__new__(ArtemisServices)
    router = EamuseRouter()
    services.game_codes = ("M39",)
    services.register(router)
    assert {
        "pcbtracker.keepalive",
        "eacoin.getpricelist",
        "eacoin.opcheckin",
        "pkglist.nr_entry",
        "sidmgr.open",
    } <= set(router._routes["M39"])


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
                "@attr": {"model": "M39:J:D:A:2026041500"},
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
    service_items = results["services"][1]["response"]["services"]["item"]
    assert any(item["@attr"]["name"] == "local2" for item in service_items)
    assert any(item["@attr"]["name"] == "lobby2" for item in service_items)
    local_service = next(item for item in service_items if item["@attr"]["name"] == "local2")
    assert local_service["@attr"]["url"] == "https://public.example/"
    keepalive_service = next(item for item in service_items if item["@attr"]["name"] == "keepalive")
    assert keepalive_service["@attr"]["url"].startswith("https://192.0.2.10/core/keepalive?")
