from __future__ import annotations

import base64
from typing import Any, Iterable


# Helpers 

def _b64(b: bytes) -> str:
    """JSON-safe payload for the websocket client."""
    return base64.b64encode(b).decode("ascii")


def _as_bytes(x: Any) -> bytes:
    """Robustly coerce various inputs to a single byte we can reason about."""
    if isinstance(x, (bytes, bytearray)):
        return bytes(x)
    if isinstance(x, str):
        # Might be an option string ("Low"), or base64 ("AQ=="), or hex ("01")
        xs = x.strip()
        try:
            # base64 path
            dec = base64.b64decode(xs, validate=True)
            if dec:
                return bytes(dec[:1])
        except Exception:
            pass
        # hex-ish path
        if len(xs) in (1, 2):
            try:
                return bytes([int(xs, 16)])
            except Exception:
                pass
    if isinstance(x, bool):
        return b"\x01" if x else b"\x00"
    try:
        iv = int(x)
        return bytes([max(0, min(255, iv))])
    except Exception:
        return b"\x00"


# Converters used by the registry AND the Select entities

class HaierHoodFanSpeedConverter:
    """
    Fan speed presets on ERD 0x5B13.

    Options exposed to the Select entity: "Off", "Low", "Medium", "High", "Boost"
    Encoded wire values: 0x00 .. 0x04
    """

    options: tuple[str, ...] = ("Off", "Low", "Medium", "High", "Boost")

    # Select helpers (entity <-> human text)
    def to_option_string(self, raw_value: Any) -> str:
        b = _as_bytes(raw_value)
        idx = b[0] if b else 0
        if 0 <= idx < len(self.options):
            return self.options[idx]
        return "Off"

    def from_option_string(self, option: str) -> str:
        """
        Return a value that our erd_encode() can consume directly.
        We return the *label* so callers can just pipe it to erd_encode().
        """
        o = (option or "").strip().lower()
        for i, name in enumerate(self.options):
            if name.lower() == o:
                # Keep it as a string; erd_encode() handles labels.
                return name
        return "Off"

    # Registry (SDK) encode/decode
    def erd_decode(self, raw: bytes | str | Any) -> bytes:
        """
        The SDK calls this when *reading* from the websocket.
        Returning the bytes keeps things maximally compatible with the rest of the HA integration,
        which already knows how to present them via to_option_string().
        """
        return _as_bytes(raw)

    def erd_encode(self, value: Any) -> str:
        """
        The SDK calls this when *writing*.
        MUST return a JSON-serializable value: we return base64 text.
        Accepts either an option label ("Low") or a numeric code (0..4).
        """
        # Map label -> index
        if isinstance(value, str) and not value.strip().isdigit():
            v = value.strip().lower()
            for i, name in enumerate(self.options):
                if name.lower() == v:
                    return _b64(bytes([i]))
            return _b64(b"\x00")

        # Numeric-ish path
        b = _as_bytes(value)
        code = max(0, min(4, b[0] if b else 0))
        return _b64(bytes([code]))


class HaierHoodLightLevelConverter:
    """
    Light level on ERD 0x5B17 (simple on/off).

    Options: "Off", "On"
    Encoded wire values: 0x00 (Off), 0x01 (On)
    """

    options: tuple[str, ...] = ("Off", "On")

    # --- Select helpers ---
    def to_option_string(self, raw_value: Any) -> str:
        b = _as_bytes(raw_value)
        return "On" if (b and b[0] == 0x01) else "Off"

    def from_option_string(self, option: str) -> str:
        o = (option or "").strip().lower()
        return "On" if o in ("on", "1", "true", "yes") else "Off"

    # --- Registry encode/decode ---
    def erd_decode(self, raw: bytes | str | Any) -> bytes:
        return _as_bytes(raw)

    def erd_encode(self, value: Any) -> str:
        # Accept label, int, or bool; return base64 text
        if isinstance(value, str):
            v = value.strip().lower() in ("on", "1", "true", "yes")
        else:
            v = bool(value)
        return _b64(b"\x01" if v else b"\x00")
