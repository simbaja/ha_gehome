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
    """
    Return an ErdCode instance when possible, otherwise a plain string.
    Do NOT construct typing.Unions at runtime; just return one of the
    acceptable runtime types.
    """
    try:
        if ErdCode:
            return ErdCode(code)  # newer SDKs
    except Exception:
        pass
    return code  # oldest SDKs accept raw strings


# Haier hood ERDs (documented from device traffic)
ERD_HAIER_HOOD_FAN_SPEED: ErdCodeStr = _erd("0x5B13")
ERD_HAIER_HOOD_LIGHT_LEVEL: ErdCodeStr = _erd("0x5B15")


#  Value enums with helpers 
class HaierHoodFanSpeed(IntEnum):
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    BOOST = 4

    def stringify(self) -> str:
        return {
            0: "Off",
            1: "Low",
            2: "Medium",
            3: "High",
            4: "Boost",
        }[int(self)]


class HaierHoodLightLevel(IntEnum):
    # Device reports 0..4 with 4 meaning "Max"
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    MAX = 4

    def stringify(self) -> str:
        return {
            0: "Off",
            1: "Low",
            2: "Medium",
            3: "High",
            4: "Max",
        }[int(self)]
