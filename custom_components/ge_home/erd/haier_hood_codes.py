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
# Fan speed: 0..4  (Off/Low/Medium/High/Boost)
ERD_HAIER_HOOD_FAN_SPEED: ErdCodeStr = _erd("0x5B13")

# Light is actually a binary on/off on this model.
# Correct ERD for light on/off:
ERD_HAIER_HOOD_LIGHT_ONOFF: ErdCodeStr = _erd("0x5B17")

# Back-compat alias (older entity code imported this symbol):
# Keep the name but point it to the correct on/off ERD.
ERD_HAIER_HOOD_LIGHT_LEVEL: ErdCodeStr = ERD_HAIER_HOOD_LIGHT_ONOFF  # alias


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
