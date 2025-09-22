"""Byte<->Enum converters for Haier hood ERDs."""
from __future__ import annotations
from typing import Any, Iterable

from .haier_hood_codes import HaierHoodFanSpeed, HaierHoodLightLevel


class _BaseByteToEnum:
    """SDK-compatible converter + helpers for HA select entities."""

    _enum = None  # override to a concrete Enum with .stringify()

    #  helpers
    def _as_int(self, val: Any) -> int:
        # Accept raw bytes
        if isinstance(val, (bytes, bytearray)):
            return int(val[0])

        # Accept booleans (useful for on/off light)
        if isinstance(val, bool):
            return 1 if val else 0

        # Accept enum
        if isinstance(val, self._enum):
            return int(val)  # enum value is its integer

        # Accept int
        if isinstance(val, int):
            return val

        # Accept strings like "Low", "Off", "2", etc.
        s = str(val).strip()
        if s.isdigit():
            return int(s)

        sl = s.lower()
        for member in self._enum:  # type: ignore
            try:
                if member.stringify().lower() == sl or member.name.lower() == sl:
                    return int(member)
            except Exception:
                # fall back to name match only if stringify not present
                if member.name.lower() == sl:
                    return int(member)

        raise ValueError(f"Unsupported value for {self.__class__.__name__}: {val!r}")

    #  SDK registry protocol (byte <-> enum)
    def erd_decode(self, raw: bytes) -> Any:
        return self._enum(self._as_int(raw))  # type: ignore

    def erd_encode(self, value: Any) -> bytes:
        return bytes([self._as_int(value)])

    #  HA select helpers (what GeErdSelect expects)
    @property
    def options(self) -> list[str]:
        opts: Iterable[str] = []
        try:
            opts = (m.stringify() for m in self._enum)  # type: ignore
        except Exception:
            opts = (m.name for m in self._enum)  # type: ignore
        return [str(o) for o in opts]

    def to_option_string(self, value: Any) -> str:
        enum_val = self._enum(self._as_int(value))  # type: ignore
        try:
            return enum_val.stringify()
        except Exception:
            return enum_val.name

    def from_option_string(self, option: str) -> Any:
        """Return the enum (SDK will encode to bytes via erd_encode)."""
        return self._enum(self._as_int(option))  # type: ignore


class HaierHoodFanSpeedConverter(_BaseByteToEnum):
    _enum = HaierHoodFanSpeed


class HaierHoodLightLevelConverter(_BaseByteToEnum):
    """Binary On/Off for light (kept as *Level* for back-compat)."""
    _enum = HaierHoodLightLevel
