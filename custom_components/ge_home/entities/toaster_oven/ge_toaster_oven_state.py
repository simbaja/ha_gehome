"""GE Home toaster oven state sensor."""

from datetime import timedelta

from propcache.api import cached_property

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory, UnitOfTime
from gehomesdk import (
    ErdCode,
    ErdToasterOvenCookMode,
    ErdToasterOvenState,
    ToasterOvenCookSetting,
)

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdBinarySensor, GeErdSensor


class GeToasterOvenCookModeSensor(GeErdSensor):
    """Sensor describing the toaster oven's selected cook mode."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            ErdCode.TOASTER_OVEN_COOK_SETTING,
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
        setting = self._current_setting
        if setting is None or setting.cook_mode is None:
            return None
        return self._stringify(setting.cook_mode)

    @property
    def _current_setting(self) -> ToasterOvenCookSetting | None:
        try:
            setting = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if not isinstance(setting, ToasterOvenCookSetting):
            return None
        return setting


class GeToasterOvenCrispFinishSensor(GeErdBinarySensor):
    """Sensor describing whether Crisp Finish is selected."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            ErdCode.TOASTER_OVEN_COOK_SETTING,
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
        setting = self._current_setting
        if setting is None:
            return None
        return setting.cook_mode == ErdToasterOvenCookMode.CRISP_FINISH

    @property
    def _current_setting(self) -> ToasterOvenCookSetting | None:
        try:
            setting = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if not isinstance(setting, ToasterOvenCookSetting):
            return None
        return setting


class GeToasterOvenConvectionSensor(GeErdBinarySensor):
    """Sensor describing whether convection is enabled."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            ErdCode.TOASTER_OVEN_CONVECTION,
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


class GeToasterOvenStateSensor(GeErdSensor):
    """Sensor describing the toaster oven's current state."""

    def __init__(self, api: ApplianceApi):
        self._cook_time_remaining_erd = api.appliance.translate_erd_code(
            ErdCode.TOASTER_OVEN_COOK_TIME_REMAINING
        )
        super().__init__(
            api,
            ErdCode.TOASTER_OVEN_CURRENT_STATE,
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
        try:
            state = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None

        if state == ErdToasterOvenState.INITIALIZATION:
            if self._cook_time_remaining > 0:
                return "Awaiting Start"
            return "Complete"
        return self._stringify(state)

    @property
    def _cook_time_remaining(self) -> int:
        try:
            value = self.appliance.get_erd_value(self._cook_time_remaining_erd)
        except KeyError:
            return 0
        if isinstance(value, timedelta):
            return int(value.total_seconds())
        try:
            return int(value or 0)
        except (TypeError, ValueError):
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
            ErdCode.TOASTER_OVEN_COOK_TIME_REMAINING,
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
