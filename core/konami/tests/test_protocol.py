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


def test_dotted_method_detection():
    assert KonamiServlet._find_call(
        {"posevent": [{"@attr": {"method": "income"}}, {"@attr": {"method": "sales"}}]}
    ) == ("posevent", "income.sales")
