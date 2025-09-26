"""ERD code constants and simple enums for Haier hood (SDK-version-safe)."""
from __future__ import annotations
from enum import IntEnum
from typing import Union

#  Safe ERD code type alias 
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


#  Haier hood ERDs 
# Status ERDs (read-only)
ERD_HAIER_HOOD_FAN_STATUS: ErdCodeStr = _erd("0x5B13")  # Fan speed: 0..4
ERD_HAIER_HOOD_LIGHT_STATUS: ErdCodeStr = _erd("0x5B17") # Light on/off: 0..1

# Command ERDs (write-only - HYPOTHESIS)
ERD_HAIER_HOOD_FAN_COMMAND: ErdCodeStr = _erd("0x5B15")
ERD_HAIER_HOOD_LIGHT_COMMAND: ErdCodeStr = _erd("0x5B16")

# Back-compat alias (older entity code imported this symbol):
# Keep the name but point it to the correct STATUS ERD.
ERD_HAIER_HOOD_FAN_SPEED: ErdCodeStr = ERD_HAIER_HOOD_FAN_STATUS  # alias
ERD_HAIER_HOOD_LIGHT_LEVEL: ErdCodeStr = ERD_HAIER_HOOD_LIGHT_STATUS  # alias


#  Value enums with small helpers 
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
    """Binary light for this hood (Off/On).  Name kept for back-compat."""
    OFF = 0
    ON = 1

    def stringify(self) -> str:
        return {0: "Off", 1: "On"}[int(self)]