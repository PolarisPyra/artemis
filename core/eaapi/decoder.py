import math
import struct
import io

from html import unescape

try:
    from lxml import etree
except ModuleNotFoundError:
    print("W", "lxml not found, XML strings will not be supported")
    etree = None


from .packer import Packer
from .const import (
    NAME_MAX_COMPRESSED, NAME_MAX_DECOMPRESSED, ATTR, PACK_ALPHABET, END_NODE, END_DOC, ARRAY_BIT,
    ENCODING, CONTENT, CONTENT_COMP, CONTENT_FULL, XML_ENCODING, DEFAULT_ENCODING, Type
)
from .misc import unpack, py_encoding, assert_true
from .node import XMLNode
from .exception import DecodeError


class Decoder:
    def __init__(self, packet):
        self.stream = io.BytesIO(packet)
        self.is_xml_string = packet.startswith(b"<")
        self.encoding = None
        self.compressed = False
        self.has_data = False
        self.packer = None

    @classmethod
    def decode(cls, packet):
        return cls(packet).unpack()

    def read(self, s_format, single=True, align=True):
        if s_format == "S":
            length = self.read("L")
            if self.packer:
                self.packer.notify_skipped(length)
            return self.stream.read(length)
        if s_format == "s":
            length = self.read("L")
            if self.packer:
                self.packer.notify_skipped(length)
            raw = self.stream.read(length)
            return raw.decode(py_encoding(self.encoding or DEFAULT_ENCODING)).rstrip("\0")

        length = struct.calcsize("=" + s_format)
        if self.packer and align:
            self.stream.seek(self.packer.request_allocation(length))
        data = self.stream.read(length)
        assert_true(len(data) == length, "EOF reached", DecodeError)
        value = struct.unpack(">" + s_format, data)
        return value[0] if single else value

    def _read_node_value(self, node: XMLNode) -> None:
        fmt = node.type.value.fmt
        count = 1
        if node.is_array:
            length = struct.calcsize("=" + fmt)
            nbytes = self.read("I")
            assert isinstance(nbytes, int)
            count = nbytes // length
            values = []
            for _ in range(count):
                values.append(self.read(fmt, single=len(fmt) == 1, align=False))

            assert self.packer is not None
            self.packer.notify_skipped(count * length)
            node.value = values
        else:
            node.value = self.read(fmt, single=len(fmt) == 1)

    def _read_metadata_name(self) -> str:
        length = self.read("B")
        assert isinstance(length, int)

        if not self.compressed:
            if length < 0x80:
                assert_true(length >= 0x40, "Invalid name length", DecodeError)
                # i.e. length = (length & ~0x40) + 1
                length -= 0x3f
            else:
                extra = self.read("B")
                assert isinstance(extra, int)
                length = (length << 8) | extra
                # i.e. length = (length & ~0x8000) + 0x41
                length -= 0x7fbf
                assert_true(length <= NAME_MAX_DECOMPRESSED, "Name length too long", DecodeError)

            name = self.stream.read(length)
            assert_true(len(name) == length, "Not enough bytes to read name", DecodeError)
            return name.decode(self.encoding or "")

        out = ""
        if length == 0:
            return out

        assert_true(length <= NAME_MAX_COMPRESSED, "Name length too long", DecodeError)

        no_bytes = math.ceil((length * 6) / 8)
        unpacked = unpack(self.stream.read(no_bytes), 6)[:length]
        return "".join(PACK_ALPHABET[i] for i in unpacked)

    def _read_metadata(self, type_):
        name = self._read_metadata_name()
        node = XMLNode(name, type_, None, encoding=self.encoding or DEFAULT_ENCODING)

        while (child := self.read("B")) != END_NODE:
            if child == ATTR:
                attr = self._read_metadata_name()
                assert_true(not attr.startswith("__"), "Invalid binary node name", DecodeError)
                # Abuse the array here to maintain order
                node.children.append(attr)
            else:
                node.children.append(self._read_metadata(child))

        if type_ & ARRAY_BIT:
            node.value = []
        return node

    def _read_databody(self, node: XMLNode):
        self._read_node_value(node)

        children = list(node.children)
        node.children = []
        for i in children:
            if isinstance(i, XMLNode):
                node.children.append(self._read_databody(i))
            else:
                node[i] = self.read("s")

        return node

    def _read_magic(self):
        magic, contents, enc, enc_comp = struct.unpack(">BBBB", self.stream.read(4))

        assert_true(magic == 0xA0, "Not a packet", DecodeError)
        assert_true(~enc & 0xFF == enc_comp, "Malformed packet header", DecodeError)
        assert_true(enc in ENCODING, "Unknown packet encoding", DecodeError)
        assert_true(contents in CONTENT, "Invalid packet contents", DecodeError)
        self.compressed = contents in CONTENT_COMP
        self.has_data = contents in CONTENT_FULL or contents == 0x44
        self.encoding = ENCODING[enc]

    def _read_xml_string(self):
        assert_true(etree is not None, "lxml missing", DecodeError)
        assert etree is not None

        parser = etree.XMLParser(remove_comments=True)
        tree = etree.XML(self.stream.read(), parser)
        self.encoding = XML_ENCODING[tree.getroottree().docinfo.encoding.upper()]
        self.compressed = False
        self.has_data = True

        def walk(node):
            attrib = {**node.attrib}
            type_str = attrib.pop("__type", "void")
            for i in Type:
                if type_str in i.value.names:
                    type_ = i
                    break
            else:
                raise ValueError("Invalid node type")
            attrib.pop("__size", None)
            count = attrib.pop("__count", None)

            is_array = count is not None
            count = 1 if count is None else int(count)

            d_type = type_.value

            if d_type.size == 1 and not is_array:
                try:
                    value = d_type._parse(node.text or "")
                except ValueError:
                    print(f"Failed to parse {node.tag} ({d_type.names[0]}): {repr(node.text)}")
                    raise
            else:
                data = node.text.split(" ")

                value = []
                for i in range(0, len(data), d_type.size):
                    value.append(d_type._parse(data[i:i+d_type.size]))
                if not is_array:
                    value = value[0]

            xml_node = XMLNode(node.tag, type_, value, encoding=self.encoding or DEFAULT_ENCODING)
            for i in node.getchildren():
                xml_node.children.append(walk(i))

            for i in attrib:
                xml_node[i] = unescape(attrib[i])

            return xml_node

        return walk(tree)

    def unpack(self):
        try:
            return self._unpack()
        except struct.error as e:
            raise DecodeError(e)

    def _unpack(self):
        if self.is_xml_string:
            return self._read_xml_string()

        self._read_magic()

        header_len = self.read("I")
        assert isinstance(header_len, int)
        start = self.stream.tell()
        schema = self._read_metadata(self.read("B"))
        assert_true(self.read("B") == END_DOC, "Unterminated schema", DecodeError)
        padding = header_len - (self.stream.tell() - start)
        assert_true(padding >= 0, "Invalid schema definition", DecodeError)
        assert_true(
            all(i == 0 for i in self.stream.read(padding)), "Invalid schema padding", DecodeError
        )

        body_len = self.read("I")
        assert isinstance(body_len, int)
        start = self.stream.tell()
        self.packer = Packer(start)
        data = self._read_databody(schema)
        self.stream.seek(self.packer.request_allocation(0))
        padding = body_len - (self.stream.tell() - start)
        assert_true(padding >= 0, "Data shape not match schema", DecodeError)
        assert_true(
            all(i == 0 for i in self.stream.read(padding)), "Invalid data padding", DecodeError
        )

        assert_true(self.stream.read(1) == b"", "Trailing data unconsumed", DecodeError)

        return data


__all__ = ("Decoder", )
