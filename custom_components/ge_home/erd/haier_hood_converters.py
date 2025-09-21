"""Byte<->Enum converters for Haier/FPA hood ERDs."""
from __future__ import annotations

from typing import Any, Iterable

from .haier_hood_codes import HaierHoodFanSpeed, HaierHoodLightLevel


class _BaseByteToEnum:
    """SDK-compatible converter + helpers for HA select entities."""

    _enum = None  # override to a concrete Enum with .stringify()

    #  helpers
    def _as_int(self, val: Any) -> int:
        # Already numeric/enum?
        if isinstance(val, (bytes, bytearray)):
            # ERDs here are single-byte values
            return int(val[0]) if val else 0
        if isinstance(val, self._enum):  # type: ignore[arg-type]
            return int(val)
        if isinstance(val, int):
            return val

        # Strings: label ("Low"), decimal ("2"), or hex ("0x02"/"02")
        s = str(val).strip()
        sl = s.lower()

        # hex-like?
        if sl.startswith("0x"):
            try:
                return int(sl, 16)
            except Exception:
                pass
        if len(sl) in (1, 2) and all(c in "0123456789abcdef" for c in sl):
            # tolerate "02" style
            try:
                return int(sl, 16)
            except Exception:
                pass

        # plain decimal
        if s.isdigit():
            return int(s)

        # label or enum name
        for member in self._enum:  # type: ignore[operator]
            try:
                if member.stringify().lower() == sl:
                    return int(member)
            except Exception:
                pass
            if member.name.lower() == sl:
                return int(member)

        raise ValueError(f"Unsupported value for {self.__class__.__name__}: {val!r}")

    #  SDK registry protocol (byte <-> enum)
    def erd_decode(self, raw: bytes) -> Any:
        return self._enum(self._as_int(raw))  # type: ignore[call-arg]

    def erd_encode(self, value: Any) -> bytes:
        return bytes([self._as_int(value)])

    #  HA select helpers (what GeErdSelect expects)
    @property
    def options(self) -> list[str]:
        opts: Iterable[str] = []
        try:
            opts = (m.stringify() for m in self._enum)  # type: ignore[attr-defined]
        except Exception:
            opts = (m.name for m in self._enum)  # type: ignore[attr-defined]
        return [str(o) for o in opts]

    def to_option_string(self, value: Any) -> str:
        enum_val = self._enum(self._as_int(value))  # type: ignore[call-arg]
        try:
            return enum_val.stringify()
        except Exception:
            return enum_val.name

    def from_option_string(self, option: str) -> Any:
        """Return the enum (SDK will encode to bytes via erd_encode)."""
        return self._enum(self._as_int(option))  # type: ignore[call-arg]


class HaierHoodFanSpeedConverter(_BaseByteToEnum):
    _enum = HaierHoodFanSpeed


class HaierHoodLightLevelConverter(_BaseByteToEnum):
    _enum = HaierHoodLightLevel
