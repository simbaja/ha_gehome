"""GE Home toaster oven state sensor."""

from propcache.api import cached_property

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory, UnitOfTime
from gehomesdk import ErdCode

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdBinarySensor, GeErdSensor
from .const import TOASTER_OVEN_COOK_MODE_MAP_REVERSE


TOASTER_OVEN_SETTING_ERD = "0x9207"
TOASTER_OVEN_STATE_ERD = "0x9209"
TOASTER_OVEN_CONVECTION_ERD = "0x922B"
TOASTER_OVEN_COOK_TIME_REMAINING_ERD = "0x922F"
TOASTER_OVEN_STATE_MAP = {
    "00": "Off",
    "03": "Cooking",
    "04": "Cooking",
}


class GeToasterOvenCookModeSensor(GeErdSensor):
    """Sensor describing the toaster oven's selected cook mode."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            TOASTER_OVEN_SETTING_ERD,
            "toaster_oven_cook_mode",
            "mdi:toaster-oven",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_toaster_oven_cook_mode"

    @cached_property
    def name(self) -> str | None:
        return f"{self.serial_or_mac} Toaster Oven Cook Mode"

    @property
    def native_value(self) -> str | None:  # type: ignore
        raw = self.appliance.get_raw_erd_value(self.erd_code)
        if raw is None:
            return None
        try:
            data = bytes.fromhex(raw)
        except ValueError:
            return None
        if len(data) < 10:
            return None

        mode = int.from_bytes(data[8:10], "big")
        return TOASTER_OVEN_COOK_MODE_MAP_REVERSE.get(mode, f"Unknown ({mode})")


class GeToasterOvenCrispFinishSensor(GeErdBinarySensor):
    """Sensor describing whether Crisp Finish is selected."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            TOASTER_OVEN_SETTING_ERD,
            "toaster_oven_crisp_finish",
            "mdi:fan",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_toaster_oven_crisp_finish"

    @cached_property
    def name(self) -> str | None:
        return f"{self.serial_or_mac} Toaster Oven Crisp Finish"

    @property
    def is_on(self) -> bool | None:  # type: ignore
        raw = self.appliance.get_raw_erd_value(self.erd_code)
        if raw is None:
            return None
        try:
            data = bytes.fromhex(raw)
        except ValueError:
            return None
        if len(data) < 10:
            return None

        mode = int.from_bytes(data[8:10], "big")
        return TOASTER_OVEN_COOK_MODE_MAP_REVERSE.get(mode) == "Crisp Finish"


class GeToasterOvenConvectionSensor(GeErdBinarySensor):
    """Sensor describing whether convection is enabled."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            TOASTER_OVEN_CONVECTION_ERD,
            "toaster_oven_convection",
            "mdi:fan",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_toaster_oven_convection"

    @cached_property
    def name(self) -> str | None:
        return f"{self.serial_or_mac} Toaster Oven Convection"

    @property
    def is_on(self) -> bool | None:  # type: ignore
        raw = self.appliance.get_raw_erd_value(self.erd_code)
        if raw is None:
            return None
        return raw != "00"


class GeToasterOvenStateSensor(GeErdSensor):
    """Sensor describing the toaster oven's current state."""

    def __init__(self, api: ApplianceApi):
        self._cook_time_remaining_erd = api.appliance.translate_erd_code(
            TOASTER_OVEN_COOK_TIME_REMAINING_ERD
        )
        super().__init__(
            api,
            TOASTER_OVEN_STATE_ERD,
            "toaster_oven_current_state",
            "mdi:toaster-oven",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_toaster_oven_current_state"

    @cached_property
    def name(self) -> str | None:
        return f"{self.serial_or_mac} Toaster Oven Current State"

    @property
    def icon(self) -> str | None:
        return "mdi:toaster-oven"

    @property
    def native_value(self) -> str | None:  # type: ignore
        raw = self.appliance.get_raw_erd_value(self._erd_code)
        if raw is None:
            return None

        normalized = raw.upper()
        if normalized == "02":
            if self._cook_time_remaining > 0:
                return "Awaiting Start"
            return "Complete"
        return TOASTER_OVEN_STATE_MAP.get(normalized, f"Unknown ({normalized})")

    @property
    def _cook_time_remaining(self) -> int:
        raw = self.appliance.get_raw_erd_value(self._cook_time_remaining_erd)
        if raw is None:
            return 0
        try:
            return int(raw, 16)
        except ValueError:
            return 0


class GeToasterOvenRemoteEnabledSensor(GeErdBinarySensor):
    """Sensor describing whether remote auto-start is enabled."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            ErdCode.UPPER_OVEN_REMOTE_ENABLED,
            "toaster_oven_remote_enabled",
            "mdi:toaster-oven",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_toaster_oven_remote_enabled"

    @cached_property
    def name(self) -> str | None:
        return f"{self.serial_or_mac} Toaster Oven Remote Enabled"


class GeToasterOvenCookTimeRemainingSensor(GeErdSensor):
    """Sensor describing toaster oven cook time remaining."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            TOASTER_OVEN_COOK_TIME_REMAINING_ERD,
            "toaster_oven_cook_time_remaining",
            "mdi:timer-outline",
            device_class_override=SensorDeviceClass.DURATION,
            uom_override=UnitOfTime.SECONDS,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_toaster_oven_cook_time_remaining"

    @cached_property
    def name(self) -> str | None:
        return f"{self.serial_or_mac} Toaster Oven Cook Time Remaining"

    @property
    def native_value(self) -> int | None:  # type: ignore
        raw = self.appliance.get_raw_erd_value(self.erd_code)
        if raw is None:
            return None
        try:
            return int(raw, 16)
        except ValueError:
            return None
