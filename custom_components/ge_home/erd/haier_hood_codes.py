"""ERD code constants and simple enums for Haier hood (SDK-version-safe)."""
from __future__ import annotations
from enum import IntEnum
from typing import Union

# Safe ERD code type alias 
try:
    # Some SDKs expose ErdCode; others only accept strings.
    from gehomesdk.erd import ErdCode  # type: ignore
    ErdCodeStr = Union["ErdCode", str]
except Exception:
    ErdCode = None  # type: ignore
    ErdCodeStr = str


def _erd(code: str) -> ErdCodeStr:
    """Return an ErdCode instance when available else the plain string."""
    try:
        if ErdCode:
            return ErdCode(code)  # ok on newer SDKs
    except Exception:
        pass
    return code  # fallback: plain string works on all SDKs

# Fan speed preset (works on this model)
ERD_HAIER_HOOD_FAN_SPEED: ErdCodeStr = _erd("0x5B13")

# Light is a simple on/off on this hood
ERD_HAIER_HOOD_LIGHT_ON: ErdCodeStr = _erd("0x5B17")

# Value enums with small helpers 
class HaierHoodFanSpeed(IntEnum):
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    BOOST = 4

    def stringify(self) -> str:
        return {0: "Off", 1: "Low", 2: "Medium", 3: "High", 4: "Boost"}[int(self)]


class HaierHoodLightState(IntEnum):
    OFF = 0
    ON = 1

    def stringify(self) -> str:
        return {0: "Off", 1: "On"}[int(self)]
