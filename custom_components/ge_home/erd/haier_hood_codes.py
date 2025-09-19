"""ERD code constants and simple enums for Haier hood (SDK-version-safe)."""
from __future__ import annotations
from enum import IntEnum
from typing import Union

# --- Safe ERD code type alias ------------------------------------------------
try:
    # Some SDKs expose ErdCode; others only accept strings.
    from gehomesdk.erd import ErdCode  # type: ignore
    ErdCodeStr = Union["ErdCode", str]
except Exception:
    ErdCode = None  # type: ignore
    ErdCodeStr = str

# Do **NOT** instantiate ErdCodeType()/typing.Union. Use string or ErdCode.
def _erd(code: str) -> ErdCodeStr:
    try:
        if ErdCode:
            return ErdCode(code)  # ok on newer SDKs
    except Exception:
        pass
    return code  # fallback: plain string works on all SDKs

ERD_HAIER_HOOD_FAN_SPEED: ErdCodeStr = _erd("0x5B13")
ERD_HAIER_HOOD_LIGHT_LEVEL: ErdCodeStr = _erd("0x5B15")

# --- Value enums with small helpers ------------------------------------------
class HaierHoodFanSpeed(IntEnum):
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    BOOST = 4
    def stringify(self) -> str:
        return {0: "Off", 1: "Low", 2: "Medium", 3: "High", 4: "Boost"}[int(self)]

class HaierHoodLightLevel(IntEnum):
    OFF = 0
    DIM = 1
    HIGH = 2
    def stringify(self) -> str:
        return {0: "Off", 1: "Dim", 2: "High"}[int(self)]
