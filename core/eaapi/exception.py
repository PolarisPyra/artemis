class EAAPIException(Exception):
    pass


class CheckFailed(EAAPIException):
    pass


class InvalidCard(CheckFailed):
    pass


class DecodeError(CheckFailed):
    pass


class EncodeError(CheckFailed):
    pass


class InvalidModel(EAAPIException):
    pass


class XMLStrutureError(EAAPIException):
    pass


class NodeNotFound(XMLStrutureError, IndexError):
    pass


class AttributeNotFound(XMLStrutureError, KeyError):
    pass
