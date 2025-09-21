"""ERD code constants and simple enums for Haier/FPA hood (SDK-version-safe)."""
from __future__ import annotations

from enum import IntEnum
from typing import Union

try:
    # Some SDKs expose ErdCode; others only accept plain strings.
    from gehomesdk.erd import ErdCode  # type: ignore
    ErdCodeStr = Union["ErdCode", str]
except Exception:  # SDK without ErdCode type
    ErdCode = None  # type: ignore
    ErdCodeStr = str


def _erd(code_hex: str) -> ErdCodeStr:
    """Return an ErdCode instance when available, else the '0xNNNN' string."""
    try:
        if ErdCode:
            return ErdCode(code_hex)  # type: ignore[arg-type]
    except Exception:
        pass
    return code_hex


# Integers (useful for dict-based registries that key by int)
ERD_HAIER_HOOD_FAN_SPEED_INT: int = 0x5B13
ERD_HAIER_HOOD_LIGHT_LEVEL_INT: int = 0x5B15

# Canonical hex strings (some SDK registries key by string)
ERD_HAIER_HOOD_FAN_SPEED_STR: str = "0x5B13"
ERD_HAIER_HOOD_LIGHT_LEVEL_STR: str = "0x5B15"

# Default public constants (ErdCode object when present, else string)
ERD_HAIER_HOOD_FAN_SPEED: ErdCodeStr = _erd(ERD_HAIER_HOOD_FAN_SPEED_STR)
ERD_HAIER_HOOD_LIGHT_LEVEL: ErdCodeStr = _erd(ERD_HAIER_HOOD_LIGHT_LEVEL_STR)


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
