import asyncio
import hashlib

from starlette.requests import Request

from core.konami.encryption import KonmaiEncrypt
from core.konami.lzkn import deflate, deflate_dummy, inflate
from core.konami.xml import data_to_xml, xml_to_data
from core.konami.xml import detect_xml_encoding
from core.konami.kbin import decode as kbin_decode, encode as kbin_encode
from core.konami.app import KonamiServlet
from konami.titles.popn.repository import PopnRepository


def test_konmai_encrypt_round_trip():
    key = KonmaiEncrypt("1-01020304-0506")
    assert key.public_key == "1-01020304-0506"
    assert KonmaiEncrypt(key.public_key).crypt(key.crypt(b"hello")) == b"hello"


def test_lzkn_literal_round_trip():
    payload = b"a small payload for konami"
    assert inflate(deflate_dummy(payload)) == payload


def test_lz_kn_matches_reference_encoder():
    payload = b"The quick brown fox jumps over the lazy dog " * 30
    encoded = deflate(payload)
    assert hashlib.sha256(encoded).hexdigest() == (
        "ffa88f70fdeb8a962b30e3d2e4b51960b731e3bd698b61dd30ddf25914249d5e"
    )


def test_xml_asphyxia_shape_round_trip():
    payload = {
        "call": {
            "@attr": {"model": "K39:2020010100"},
            "game": {"@attr": {"method": "get"}},
        }
    }
    assert xml_to_data(data_to_xml(payload))["call"]["game"]["@attr"]["method"] == "get"


def test_xml_declared_shift_jis_round_trip():
    payload = {"call": {"playerdata": {"@attr": {"name": "ポップン"}}}}
    encoded = data_to_xml(payload, "shift_jis")
    assert detect_xml_encoding(encoded) == "shift_jis"
    assert xml_to_data(encoded)["call"]["playerdata"]["@attr"]["name"] == "ポップン"


def test_xml_typed_binary_and_quoted_attributes():
    encoded = data_to_xml(
        {
            "response": {
                "playerdata": {
                    "town": {
                        "@attr": {"__type": "bin", "label": 'a"b'},
                        "@content": bytes.fromhex("00ff10"),
                    },
                    "address": {
                        "@attr": {"__type": "ip4"},
                        "@content": [0x7F000001],
                    },
                }
            }
        }
    )
    text = encoded.decode("utf-8")
    assert 'label="a\'b&quot;b"' in text or "label='a\"b'" in text
    assert ">00ff10<" in text
    assert ">127.0.0.1<" in text
    decoded = xml_to_data(encoded)
    assert decoded["response"]["playerdata"]["town"]["@content"] == bytes.fromhex(
        "00ff10"
    )
    assert decoded["response"]["playerdata"]["address"]["@content"] == [
        0x7F000001
    ]


def test_xml_typed_boolean_and_numeric_arrays():
    encoded = data_to_xml(
        {
            "response": {
                "playerdata": {
                    "enabled": {"@attr": {"__type": "bool"}, "@content": [False]},
                    "values": {
                        "@attr": {"__type": "s16", "__count": 3},
                        "@content": [1, -2, 3],
                    },
                }
            }
        }
    )
    text = encoded.decode("utf-8")
    assert ">0<" in text
    decoded = xml_to_data(encoded)
    playerdata = decoded["response"]["playerdata"]
    assert playerdata["enabled"]["@content"] == [0]
    assert playerdata["values"]["@content"] == [1, -2, 3]


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


def test_kbin_group_and_vector_round_trip():
    payload = {
        "response": {
            "playerdata": {
                "position": {
                    "@attr": {"__type": "3f"},
                    "@content": [1.0, 2.0, 3.0],
                },
                "flags": {
                    "@attr": {"__type": "vu8", "__count": 2},
                    "@content": list(range(32)),
                },
            }
        }
    }
    decoded, _ = kbin_decode(kbin_encode(payload, "utf-8", True))
    assert decoded["response"]["playerdata"]["position"]["@content"] == [
        1.0,
        2.0,
        3.0,
    ]
    assert decoded["response"]["playerdata"]["flags"]["@attr"]["__count"] == 2


def test_dotted_method_detection():
    assert KonamiServlet._find_call(
        {"posevent": [{"@attr": {"method": "income"}}, {"@attr": {"method": "sales"}}]}
    ) == ("posevent", "income.sales")


def test_malformed_xml_is_rejected():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "server": ("localhost", 80),
        "scheme": "http",
    }

    async def receive():
        return {"type": "http.request", "body": b"<not-xml", "more_body": False}

    response = asyncio.run(KonamiServlet().handle(Request(scope, receive)))
    assert response.status_code == 404


def test_popn_score_sharing_is_scoped_to_refid():
    class ScoreStore:
        def __init__(self):
            self.requested_refid = None

        async def documents(self, game_code, collection, version="", refid=""):
            self.requested_refid = refid
            return [
                (
                    refid,
                    {
                        "scores": {
                            "1:0": {"score": 100, "cnt": 1, "clear_type": 100}
                        }
                    },
                )
            ]

        async def get_document(self, *args):
            return None

    store = ScoreStore()
    data = type(
        "Data",
        (),
        {
            "config": type(
                "Config", (), {"konami": type("Konami", (), {"enable_score_sharing": True})()}
            )(),
            "konami": store,
        },
    )()
    scores = asyncio.run(PopnRepository(data, "M39").scores("REF-A", "v24"))
    assert store.requested_refid == "REF-A"
    assert scores["scores"]["1:0"]["score"] == 100


def test_popn_webui_rival_events_match_reference_limits():
    class RivalStore:
        def __init__(self):
            self.docs = {
                ("RIVAL", "M39", "profile", ""): {"name": "Rival"},
            }

        async def get_document(self, refid, game_code, collection, version=""):
            return self.docs.get((refid, game_code, collection, version))

        async def put_document(
            self, refid, game_code, collection, document, version=""
        ):
            self.docs[(refid, game_code, collection, version)] = document

        async def documents(self, *args, **kwargs):
            return []

    store = RivalStore()
    data = type(
        "Data",
        (),
        {
            "config": type("Config", (), {})(),
            "konami": store,
        },
    )()
    repo = PopnRepository(data, "M39")
    assert asyncio.run(repo.add_rival(" OWNER ", "RIVAL"))
    assert store.docs[("OWNER", "M39", "rivals", "")]["rivals"] == ["RIVAL"]
    assert asyncio.run(repo.delete_rival("OWNER", "RIVAL"))
    assert store.docs[("OWNER", "M39", "rivals", "")]["rivals"] == []
