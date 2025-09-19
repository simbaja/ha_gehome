"""Byte<->Enum converters for Haier hood ERDs."""
from __future__ import annotations
from typing import Any, Optional
from .haier_hood_codes import HaierHoodFanSpeed, HaierHoodLightLevel

# Converters follow the simple protocol used by the SDK encoder registry:
#   - erd_decode(bytes) -> friendly value (enum)
#   - erd_encode(enum|int|str) -> bytes

class _BaseByteToEnum:
    _enum = None  # override
    def _as_int(self, val: Any) -> int:
        if isinstance(val, (bytes, bytearray)):
            return int(val[0])
        if isinstance(val, self._enum):
            return int(val)
        if isinstance(val, int):
            return val
        # string path (e.g. "Low")
        try:
            s = str(val).strip().lower()
            for member in self._enum:  # type: ignore
                if member.stringify().lower() == s or member.name.lower() == s:
                    return int(member)
        except Exception:
            pass
        raise ValueError(f"Unsupported value for {self.__class__.__name__}: {val!r}")

    # --- SDK registry protocol ---
    def erd_decode(self, raw: bytes) -> Any:
        return self._enum(self._as_int(raw))  # type: ignore

    def erd_encode(self, value: Any) -> bytes:
        return bytes([self._as_int(value)])


class HaierHoodFanSpeedConverter(_BaseByteToEnum):
    _enum = HaierHoodFanSpeed


class HaierHoodLightLevelConverter(_BaseByteToEnum):
    _enum = HaierHoodLightLevel
