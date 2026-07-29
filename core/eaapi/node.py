import binascii
import re

from typing import Generator, Any

from html import escape

from .misc import assert_true
from .const import DEFAULT_ENCODING, NAME_MAX_COMPRESSED, XML_ENCODING_BACK, Type
from .exception import XMLStrutureError, NodeNotFound, AttributeNotFound


class XMLNode:
    def __init__(self, name, type_=Type.Void, value="", attributes=None, encoding=DEFAULT_ENCODING):
        self.name = name
        self.type = type_ if isinstance(type_, Type) else Type.from_val(type_)
        self.value: Any = value  # TODO: A stricter way to do this. Subclassing?
        self.children = []
        self.attributes = {}
        if attributes is not None:
            for i in attributes:
                self.attributes[i] = attributes[i]
        self.encoding = encoding or DEFAULT_ENCODING
        assert_true(encoding in XML_ENCODING_BACK, "Invalid encoding")

    @classmethod
    def void(cls, __name, **attributes):
        return cls(__name, Type.Void, (), attributes)

    @property
    def is_array(self):
        return isinstance(self.value, list)

    @property
    def can_compress(self):
        return (
            (len(self.name) <= NAME_MAX_COMPRESSED)
            and all(i.can_compress for i in self.children)
        )

    def _xpath(self, attr, path):
        if path:
            child = path.pop(0)
            for i in self.children:
                if i.name == child:
                    return i._xpath(attr, path)
            raise NodeNotFound
        if not attr:
            return self
        if attr in self.attributes:
            return self.attributes[attr]
        raise AttributeNotFound

    def xpath(self, path):
        match = re.match(r"^(?:@([\w:]+)/)?((?:[\w:]+(?:/|$))+)", path)
        if match is None:
            raise ValueError
        attr = match.group(1)
        path = match.group(2).split("/")
        return self._xpath(attr, path)

    def append(self, __name, __type=Type.Void, __value=(), **attributes):
        child = XMLNode(__name, __type, __value, attributes)
        self.children.append(child)
        return child

    def __len__(self):
        return len(self.children)

    def __iter__(self) -> Generator["XMLNode", None, None]:
        for i in self.children:
            yield i

    def get(self, name, default=None):
        try:
            return self[name]
        except XMLStrutureError:
            return default

    def __getitem__(self, name):
        if isinstance(name, int):
            try:
                return self.children[name]
            except IndexError:
                raise NodeNotFound
        try:
            return self.attributes[name]
        except KeyError:
            raise AttributeNotFound

    def __setitem__(self, name, value):
        self.attributes[name] = value

    def to_str(self, pretty=False):
        return (
            f'<?xml version="1.0" encoding="{XML_ENCODING_BACK[self.encoding]}"?>'
            + ("\n" if pretty else "")
            + self._to_str(pretty)
        )

    def __str__(self):
        return self.to_str(pretty=True)

    def _value_str(self, value: Any) -> str:
        if isinstance(value, list):
            return " ".join(map(self._value_str, value))
        if self.type == Type.Blob:
            return binascii.hexlify(value).decode()
        if self.type == Type.IPv4 or self.type == Type.IPv4_Int:
            if isinstance(value, int):
                value = (
                    (value >> 24) & 0xff,
                    (value >> 16) & 0xff,
                    (value >> 8) & 0xff,
                    (value >> 0) & 0xff,
                )
            return f"{value[0]}.{value[1]}.{value[2]}.{value[3]}"
        if self.type in (Type.Float, Type.TwoFloat, Type.ThreeFloat):
            return f"{value:.6f}"
        if self.type == Type.Str:
            return escape(str(value))

        return str(value)

    def _to_str(self, pretty, indent=0):
        if not pretty:
            indent = 0
        nl = "\n" if pretty else ""
        tag = f"{' ' * indent}<{self.name}"

        if self.type != Type.Void:
            tag += f" __type=\"{self.type.value.names[0]}\""
        if self.type == Type.Blob:
            tag += f" __size=\"{len(self.value)}\""
        if self.is_array:
            tag += f" __count=\"{len(self.value)}\""

        attributes = " ".join(f"{i}=\"{escape(j)}\"" for i, j in self.attributes.items())
        if attributes:
            tag += " " + attributes
        tag += ">"
        if self.value is not None and self.type != Type.Void:
            if self.is_array:
                tag += " ".join(map(self._value_str, self.value))
            else:
                tag += self._value_str(self.value)
        elif not self.children:
            return tag[:-1] + (" " if pretty else "") + "/>"

        for i in self.children:
            if isinstance(i, XMLNode):
                tag += nl + i._to_str(pretty, indent + 4)
        if self.children:
            tag += nl + " " * indent
        tag += f"</{self.name}>"
        return tag

    def __eq__(self, other):
        return (
            isinstance(other, XMLNode)
            and self.name == other.name
            and self.type == other.type
            and self.value == other.value
            and len(self.children) == len(other.children)
            and all(i == j for i, j in zip(self.children, other.children))
        )


__all__ = ("XMLNode", )
