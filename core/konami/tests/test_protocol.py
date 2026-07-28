from core.konami.encryption import KonmaiEncrypt
from core.konami.lzkn import deflate_dummy, inflate
from core.konami.xml import data_to_xml, xml_to_data


def test_konmai_encrypt_round_trip():
    key = KonmaiEncrypt("1-01020304-0506")
    assert key.public_key == "1-01020304-0506"
    assert KonmaiEncrypt(key.public_key).crypt(key.crypt(b"hello")) == b"hello"


def test_lzkn_literal_round_trip():
    payload = b"a small payload for konami"
    assert inflate(deflate_dummy(payload)) == payload


def test_xml_asphyxia_shape_round_trip():
    payload = {"call": {"@attr": {"model": "K39:2020010100"}, "game": {"@attr": {"method": "get"}}}}
    assert xml_to_data(data_to_xml(payload))["call"]["game"]["@attr"]["method"] == "get"

