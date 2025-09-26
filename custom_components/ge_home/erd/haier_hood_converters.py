from __future__ import annotations
from typing import Any

# helpers

def _to_byte(v: Any) -> int:
    """Coerce a value to a single 0..255 int."""
    if isinstance(v, (bytes, bytearray)) and v:
        return v[0]
    if isinstance(v, str):
        s = v.strip().lower()
        # try simple hex like "00" / "1" first
        try:
            return max(0, min(255, int(s, 16)))
        except Exception:
            pass
        # try plain int in string
        try:
            return max(0, min(255, int(s)))
        except Exception:
            pass
        if s in ("on", "true", "yes"):
            return 1
        if s in ("off", "false", "no"):
            return 0
    try:
        return max(0, min(255, int(v)))
    except Exception:
        return 0


# Fan speed (ERD 0x5B13) 

class HaierHoodFanSpeedConverter:
    """
    Options: Off(0), Low(1), Medium(2), High(3), Boost(4)
    Encode for GE setErd: HEX STRING like "00".."04"
    """

    options = ("Off", "Low", "Medium", "High", "Boost")

    # Used by the Select entity to display a nice label
    def to_option_string(self, raw_value: Any) -> str:
        idx = _to_byte(raw_value)
        return self.options[idx] if 0 <= idx < len(self.options) else "Off"

    # Select -> value we pass on to erd_encode()
    def from_option_string(self, option: str) -> int:
        o = (option or "").strip().lower()
        for i, name in enumerate(self.options):
            if name.lower() == o:
                return i
        return 0

    # (for the entity’s “raw write” fast path)
    def to_bytes(self, option_or_value: Any) -> bytes:
        # Accept either an option label or a numeric-ish value
        if isinstance(option_or_value, str) and not option_or_value.strip().isdigit():
            code = self.from_option_string(option_or_value)
        else:
            code = _to_byte(option_or_value)
        code = max(0, min(4, code))
        return bytes([code])

    # Registry (SDK) decode/encode
    def erd_decode(self, raw: Any) -> bytes:
        # Keep bytes on reads; the integration already knows how to show them
        return self.to_bytes(raw)

    def erd_encode(self, value: Any) -> str:
        # MUST return JSON-serializable; GE expects hex strings for this ERD
        b = self.to_bytes(value)
        return f"{b[0]:02X}"


# Light level (ERD 0x5B17) 

class HaierHoodLightLevelConverter:
    """
    Options: Off(0), On(1)
    Encode for GE setErd: HEX STRING "00" or "01"
    """

    options = ("Off", "On")

    def to_option_string(self, raw_value: Any) -> str:
        return "On" if _to_byte(raw_value) == 1 else "Off"

    def from_option_string(self, option: str) -> int:
        o = (option or "").strip().lower()
        return 1 if o in ("on", "1", "true", "yes") else 0

    def to_bytes(self, option_or_value: Any) -> bytes:
        val = 0
        if isinstance(option_or_value, str):
            val = self.from_option_string(option_or_value)
        else:
            val = _to_byte(option_or_value)
        return b"\x01" if val == 1 else b"\x00"

    def erd_decode(self, raw: Any) -> bytes:
        return self.to_bytes(raw)

    def erd_encode(self, value: Any) -> str:
        # GE expects hex strings "00" or "01" for this ERD
        return "01" if _to_byte(value) == 1 else "00"