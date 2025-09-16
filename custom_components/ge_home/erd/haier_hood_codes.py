import enum
from gehomesdk import ErdCodeType

# Haier hood ERD codes
ERD_HAIER_HOOD_FAN_SPEED = ErdCodeType("0x5B13")
ERD_HAIER_HOOD_LIGHT_LEVEL = ErdCodeType("0x5B17")
# You can add more if logs show activity, e.g. 0x5B11, 0x5B15, etc.

class HaierHoodFanSpeed(enum.IntEnum):
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    BOOST = 4

    def stringify(self) -> str:
        return self.name.capitalize()

class HaierHoodLightLevel(enum.IntEnum):
    OFF = 0
    LOW = 1
    HIGH = 2

    def stringify(self) -> str:
        return self.name.capitalize()
