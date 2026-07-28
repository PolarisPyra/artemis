import asyncio

from starlette.requests import Request

from core.konami.encryption import KonmaiEncrypt
from core.konami.lzkn import deflate_dummy, inflate
from core.konami.xml import data_to_xml, xml_to_data
from core.konami.xml import detect_xml_encoding
from core.konami.kbin import decode as kbin_decode, encode as kbin_encode
from core.konami.app import KonamiServlet


def test_konmai_encrypt_round_trip():
    key = KonmaiEncrypt("1-01020304-0506")
    assert key.public_key == "1-01020304-0506"
    assert KonmaiEncrypt(key.public_key).crypt(key.crypt(b"hello")) == b"hello"


def test_lzkn_literal_round_trip():
    payload = b"a small payload for konami"
    assert inflate(deflate_dummy(payload)) == payload


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
