import struct
import io

from .packer import Packer
from .misc import pack, py_encoding, assert_true
from .const import (
    PACK_ALPHABET, DEFAULT_ENCODING, ENCODING, ENCODING_BACK, NAME_MAX_DECOMPRESSED, ARRAY_BIT,
    ATTR, END_NODE, END_DOC, CONTENT_COMP_FULL, CONTENT_COMP_SCHEMA, CONTENT_ASCII_FULL,
    CONTENT_ASCII_SCHEMA
)
from .exception import EncodeError
from .node import XMLNode


class Encoder:
    def __init__(self, encoding=DEFAULT_ENCODING):
        self.stream = io.BytesIO()
        assert_true(encoding in ENCODING_BACK, f"Unknown encoding {encoding}", EncodeError)
        self.encoding = ENCODING_BACK[encoding]
        self.packer = None
        self._compressed = False

    @classmethod
    def encode(cls, tree, xml_string=False):
        if xml_string:
            return tree.to_str(pretty=False).encode(tree.encoding)
        encoder = cls(tree.encoding)
        encoder.pack(tree)
        return encoder.stream.getvalue()

    def align(self, to=4, pad_char=b"\0"):
        if to < 2:
            return
        if (dist := self.stream.tell() % to) == 0:
            return
        self.stream.write(pad_char * (to - dist))

    def write(self, s_format, value, single=True):
        if s_format == "S":
            assert self.packer is not None
            self.write("L", len(value))
            self.stream.write(value)
            self.packer.notify_skipped(len(value))
            return
        if s_format == "s":
            assert self.packer is not None
            value = value.encode(py_encoding(ENCODING[self.encoding])) + b"\0"
            self.write("L", len(value))
            self.stream.write(value)
            self.packer.notify_skipped(len(value))
            return

        length = struct.calcsize("=" + s_format)

        if isinstance(value, list):
            assert self.packer is not None
            self.write("L", len(value) * length)
            self.packer.notify_skipped(len(value) * length)

            for x in value:
                try:
                    if single:
                        self.stream.write(struct.pack(f">{s_format}", x))
                    else:
                        self.stream.write(struct.pack(f">{s_format}", *x))
                except struct.error:
                    raise ValueError(f"Failed to pack {s_format}: {repr(x)}")
        else:
            if self.packer:
                self.stream.seek(self.packer.request_allocation(length))

            try:
                if single:
                    self.stream.write(struct.pack(f">{s_format}", value))
                else:
                    self.stream.write(struct.pack(f">{s_format}", *value))
            except struct.error:
                raise ValueError(f"Failed to pack {s_format}: {repr(value)}")

    def _write_node_value(self, type_, value):
        fmt = type_.value.fmt
        if fmt == "s":
            self.write("s", value)
        else:
            self.write(fmt, value, single=len(fmt) == 1)

    def _write_metadata_name(self, name):
        if not self._compressed:
            assert_true(len(name) <= NAME_MAX_DECOMPRESSED, "Name length too long", EncodeError)
            if len(name) > 64:
                self.write("H", len(name) + 0x7fbf)
            else:
                self.write("B", len(name) + 0x3f)
            self.stream.write(name.encode(py_encoding(ENCODING[self.encoding])))
            return

        assert_true(all(i in PACK_ALPHABET for i in name), f"Invalid schema name {name} (invalid chars)", EncodeError)
        assert_true(len(name) < 256, f"Invalid schema name {name} (too long)", EncodeError)
        self.write("B", len(name))
        if len(name) == 0:
            return

        name = bytearray(PACK_ALPHABET.index(i) for i in name)
        self.stream.write(pack(name, 6))

    def _write_metadata(self, node):
        self.write("B", node.type.value.id | (ARRAY_BIT if node.is_array else 0x00))
        self._write_metadata_name(node.name)

        for attr in node.attributes:
            self.write("B", ATTR)
            self._write_metadata_name(attr)
        for child in node:
            self._write_metadata(child)
        self.write("B", END_NODE)

    def _write_databody(self, data: XMLNode):
        self._write_node_value(data.type, data.value)

        for attr in data.attributes:
            self.align()
            self.write("s", data[attr])
        for child in data:
            self._write_databody(child)

    def _write_magic(self, has_data=True):
        if has_data:
            contents = CONTENT_COMP_FULL if self._compressed else CONTENT_ASCII_FULL
        else:
            contents = CONTENT_COMP_SCHEMA if self._compressed else CONTENT_ASCII_SCHEMA

        enc_comp = ~self.encoding & 0xFF
        self.stream.write(struct.pack(">BBBB", 0xA0, contents, self.encoding, enc_comp))

    def pack(self, node):
        try:
            return self._pack(node)
        except struct.error as e:
            return EncodeError(e)

    def _pack(self, node):
        self._compressed = node.can_compress  # Opportunically compress if we can
        self._write_magic()

        schema_start = self.stream.tell()
        self.write("I", 0)
        self._write_metadata(node)
        self.write("B", END_DOC)
        self.align()
        schema_end = self.stream.tell()
        self.stream.seek(schema_start)
        self.write("I", schema_end - schema_start - 4)

        self.stream.seek(schema_end)
        self.write("I", 0)
        self.packer = Packer(self.stream.tell())
        self._write_databody(node)
        self.stream.seek(0, io.SEEK_END)
        self.align()
        node_end = self.stream.tell()
        self.stream.seek(schema_end)
        self.packer = None
        self.write("I", node_end - schema_end - 4)


__all__ = ("Encoder", )
