import os

from pydantic_core import core_schema

# --------------------------------------------------------------------------------
class SpanId:
    def __init__(self, int_: int = None, bytes_: bytes = None, hex_: str = None):

        if [int_, bytes_, hex_].count(None) != 2:
            raise TypeError('one of the int_, bytes_ or hex_ arguments must be given')

        if int_ is not None:
            if not 0 <= int_ < 1 << 64:
                raise ValueError('int is out of range (need a 64-bit value)')

        if bytes_ is not None:
            if len(bytes_) != 8:
                raise ValueError('bytes_ is not a 8-char string')
            assert isinstance(bytes_, bytes), repr(bytes_)
            int_ = int.from_bytes(bytes_, 'big')  # big endian

        if hex_ is not None:
            if len(hex_) != 16:
                raise ValueError('badly formed hexadecimal SpanId string')
            int_ = int(hex_, 16)

        self._value: int = int_

    # ----------------------------------------------------------------------------
    @classmethod
    def _validate(cls, value) -> 'SpanId':
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(int_ = value)
        if isinstance(value, bytes):
            return cls(bytes_ = value)
        if isinstance(value, str):
            return cls(hex_ = value)
        raise ValueError(f"Cannot construct SpanId from type {type(value).__name__}")

    # ----------------------------------------------------------------------------
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v.hex,
                info_arg=False,
            )
        )

    # ----------------------------------------------------------------------------
    @property
    def value(self) -> int:
        return self._value

    @property
    def hex(self) -> str:
        return f"{self._value:016x}"

    @property
    def bytes(self) -> bytes:
        return self._value.to_bytes(8, 'big')

    # ----------------------------------------------------------------------------
    def __eq__(self, other) -> bool:
        if isinstance(other, SpanId):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"SpanId({self.hex})"

    def __str__(self) -> str:
        return self.hex

# --------------------------------------------------------------------------------
def span_id_gen() -> SpanId:
    return SpanId(bytes_ = os.urandom(8))
