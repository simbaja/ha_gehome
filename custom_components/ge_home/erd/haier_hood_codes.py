"""Haier hood ERD codes and enums used by the GE Home custom integration."""

from enum import IntEnum

# IMPORTANT: ErdCodeType is a typing alias in gehomesdk; do NOT instantiate it.
# ERD codes should be plain strings like "0x5B13".
ERD_HAIER_HOOD_FAN_SPEED: str = "0x5B13"
ERD_HAIER_HOOD_LIGHT_LEVEL: str = "0x5B15"  # change to "0x5B17" if your device uses that

class HaierHoodFanSpeed(IntEnum):
    OFF = 0x00
    LOW = 0x01
    MEDIUM = 0x02
    HIGH = 0x03
    BOOST = 0x04  # seen on some models; harmless if device doesn't support it

    def stringify(self) -> str:
        return {
            HaierHoodFanSpeed.OFF: "Off",
            HaierHoodFanSpeed.LOW: "Low",
            HaierHoodFanSpeed.MEDIUM: "Medium",
            HaierHoodFanSpeed.HIGH: "High",
            HaierHoodFanSpeed.BOOST: "Boost",
        }.get(self, f"Unknown({int(self)})")


class HaierHoodLightLevel(IntEnum):
    OFF = 0x00
    DIM = 0x01
    HIGH = 0x04  # your logs showed 0x04; if your unit has more steps, add them.

    def stringify(self) -> str:
        return {
            HaierHoodLightLevel.OFF: "Off",
            HaierHoodLightLevel.DIM: "Dim",
            HaierHoodLightLevel.HIGH: "High",
        }.get(self, f"Unknown({int(self)})")
