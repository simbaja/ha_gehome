import logging
from typing import List

from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode,
    ErdApplianceType,
    OvenConfiguration,
    ErdOvenLightLevel,
    ErdOvenLightLevelAvailability,
    ErdOvenWarmingState,
    ErdOvenCookMode,
    ErdDataType,
)

from .base import ApplianceApi
from .cooktop import build_cooktop_entities
from ..entities import (
    GeErdSensor,
    GeErdTimerSensor,
    GeErdTimerNumber,
    GeErdBinarySensor,
    GeErdSelect,
    GeErdSwitch,
    GeErdPropertySensor,
    GeOven,
    GeOvenErdTemperatureSensor,
    GeOvenErdTemperatureOffsetSensor,
    GeOvenErdCookModeSensor,
    GeOvenLightLevelSelect,
    GeOvenWarmingStateSelect,
    SoundLevelOptionsConverter,
    EndToneOptionsConverter,
    ClockFormatOptionsConverter,
    UPPER_OVEN,
    LOWER_OVEN,
)

_LOGGER = logging.getLogger(__name__)


class OvenApi(ApplianceApi):
    """API class for oven objects"""

    APPLIANCE_TYPE = ErdApplianceType.OVEN

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()
        oven_config: OvenConfiguration | None = self.try_get_erd_value(
            ErdCode.OVEN_CONFIGURATION
        )
        has_lower_oven = False
        if oven_config is not None:
            has_lower_oven = oven_config.has_lower_oven
        else:
            lower_mode = self.try_get_erd_value(ErdCode.LOWER_OVEN_COOK_MODE)
            has_lower_oven = (
                lower_mode is not None
                and getattr(lower_mode, "cook_mode", None) is not None
                and getattr(lower_mode, "cook_mode", None) != ErdOvenCookMode.NOMODE
            )

        has_upper_oven = bool(
            not has_lower_oven
            or self.has_erd_code(ErdCode.UPPER_OVEN_COOK_MODE)
            or self.has_erd_code(ErdCode.UPPER_OVEN_CURRENT_STATE)
            or self.has_erd_code(ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE)
        )

        has_upper_raw_temperature = self.has_erd_code(
            ErdCode.UPPER_OVEN_RAW_TEMPERATURE
        )
        has_lower_raw_temperature = self.has_erd_code(
            ErdCode.LOWER_OVEN_RAW_TEMPERATURE
        )

        has_upper_probe_temperature = self.has_erd_code(
            ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP
        )
        has_lower_probe_temperature = self.has_erd_code(
            ErdCode.LOWER_OVEN_PROBE_DISPLAY_TEMP
        )

        upper_light: ErdOvenLightLevel | None = self.try_get_erd_value(
            ErdCode.UPPER_OVEN_LIGHT
        )
        upper_light_availability: ErdOvenLightLevelAvailability | None = (
            self.try_get_erd_value(ErdCode.UPPER_OVEN_LIGHT_AVAILABILITY)
        )
        lower_light: ErdOvenLightLevel | None = self.try_get_erd_value(
            ErdCode.LOWER_OVEN_LIGHT
        )
        lower_light_availability: ErdOvenLightLevelAvailability | None = (
            self.try_get_erd_value(ErdCode.LOWER_OVEN_LIGHT_AVAILABILITY)
        )

        upper_warm_drawer: ErdOvenWarmingState | None = self.try_get_erd_value(
            ErdCode.UPPER_OVEN_WARMING_DRAWER_STATE
        )
        lower_warm_drawer: ErdOvenWarmingState | None = self.try_get_erd_value(
            ErdCode.LOWER_OVEN_WARMING_DRAWER_STATE
        )
        warm_drawer: ErdOvenWarmingState | None = self.try_get_erd_value(
            ErdCode.WARMING_DRAWER_STATE
        )

        _LOGGER.debug(f"Oven Config: {oven_config}")
        oven_entities = []

        if has_lower_oven:
            oven_entities.extend(
                [
                    GeOvenErdCookModeSensor(
                        self,
                        ErdCode.LOWER_OVEN_COOK_MODE,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeErdSensor(
                        self,
                        ErdCode.LOWER_OVEN_CURRENT_STATE,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeErdSensor(
                        self, ErdCode.LOWER_OVEN_COOK_TIME_REMAINING, suggested_uom="h"
                    ),
                    GeErdTimerSensor(
                        self, ErdCode.LOWER_OVEN_KITCHEN_TIMER, suggested_uom="h"
                    ),
                    GeErdTimerNumber(self, ErdCode.LOWER_OVEN_KITCHEN_TIMER),
                    GeOvenErdTemperatureOffsetSensor(
                        self,
                        ErdCode.LOWER_OVEN_USER_TEMP_OFFSET,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeOvenErdTemperatureSensor(
                        self,
                        ErdCode.LOWER_OVEN_DISPLAY_TEMPERATURE,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeErdBinarySensor(
                        self,
                        ErdCode.LOWER_OVEN_REMOTE_ENABLED,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                ]
            )
            if self._has_oven_control_erds(LOWER_OVEN):
                oven_entities.append(
                    GeOven(
                        self,
                        LOWER_OVEN,
                        True,
                        self._temperature_code(has_lower_raw_temperature),
                    )
                )
            if has_lower_raw_temperature:
                oven_entities.append(
                    GeOvenErdTemperatureSensor(
                        self,
                        ErdCode.LOWER_OVEN_RAW_TEMPERATURE,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    )
                )
            if (
                lower_light_availability is None
                or lower_light_availability.is_available
                or lower_light is not None
            ):
                oven_entities.append(
                    GeOvenLightLevelSelect(self, ErdCode.LOWER_OVEN_LIGHT)
                )
            if lower_warm_drawer is not None:
                oven_entities.append(
                    GeOvenWarmingStateSelect(
                        self, ErdCode.LOWER_OVEN_WARMING_DRAWER_STATE
                    )
                )
            if has_lower_probe_temperature:
                oven_entities.append(
                    GeOvenErdTemperatureSensor(
                        self,
                        ErdCode.LOWER_OVEN_PROBE_DISPLAY_TEMP,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    )
                )

        if has_upper_oven:
            oven_entities.extend(
                [
                    GeOvenErdCookModeSensor(
                        self,
                        ErdCode.UPPER_OVEN_COOK_MODE,
                        self._single_name(
                            ErdCode.UPPER_OVEN_COOK_MODE, not has_lower_oven
                        ),
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeErdSensor(
                        self,
                        ErdCode.UPPER_OVEN_CURRENT_STATE,
                        self._single_name(
                            ErdCode.UPPER_OVEN_CURRENT_STATE, not has_lower_oven
                        ),
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeErdSensor(
                        self,
                        ErdCode.UPPER_OVEN_COOK_TIME_REMAINING,
                        self._single_name(
                            ErdCode.UPPER_OVEN_COOK_TIME_REMAINING,
                            not has_lower_oven,
                        ),
                        suggested_uom="h",
                    ),
                    GeErdTimerSensor(
                        self,
                        ErdCode.UPPER_OVEN_KITCHEN_TIMER,
                        self._single_name(
                            ErdCode.UPPER_OVEN_KITCHEN_TIMER, not has_lower_oven
                        ),
                        suggested_uom="h",
                    ),
                    GeErdTimerNumber(
                        self,
                        ErdCode.UPPER_OVEN_KITCHEN_TIMER,
                        self._single_name(
                            ErdCode.UPPER_OVEN_KITCHEN_TIMER,
                            not has_lower_oven
                        ),
                    ),
                    GeOvenErdTemperatureOffsetSensor(
                        self,
                        ErdCode.UPPER_OVEN_USER_TEMP_OFFSET,
                        self._single_name(
                            ErdCode.UPPER_OVEN_USER_TEMP_OFFSET,
                            not has_lower_oven,
                        ),
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeOvenErdTemperatureSensor(
                        self,
                        ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE,
                        self._single_name(
                            ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE,
                            not has_lower_oven,
                        ),
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeErdBinarySensor(
                        self,
                        ErdCode.UPPER_OVEN_REMOTE_ENABLED,
                        self._single_name(
                            ErdCode.UPPER_OVEN_REMOTE_ENABLED,
                            not has_lower_oven,
                        ),
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                ]
            )
            if self._has_oven_control_erds(UPPER_OVEN):
                oven_entities.append(
                    GeOven(
                        self,
                        UPPER_OVEN,
                        has_lower_oven,
                        self._temperature_code(has_upper_raw_temperature),
                    )
                )
        if has_upper_raw_temperature:
            oven_entities.append(
                GeOvenErdTemperatureSensor(
                    self,
                    ErdCode.UPPER_OVEN_RAW_TEMPERATURE,
                    self._single_name(
                        ErdCode.UPPER_OVEN_RAW_TEMPERATURE,
                        not has_lower_oven,
                    ),
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )
        if (
            upper_light_availability is None
            or upper_light_availability.is_available
            or upper_light is not None
        ):
            oven_entities.append(
                GeOvenLightLevelSelect(
                    self,
                    ErdCode.UPPER_OVEN_LIGHT,
                    self._single_name(
                        ErdCode.UPPER_OVEN_LIGHT, not has_lower_oven
                    ),
                )
            )
        if upper_warm_drawer is not None:
            oven_entities.append(
                GeOvenWarmingStateSelect(
                    self,
                    ErdCode.UPPER_OVEN_WARMING_DRAWER_STATE,
                    self._single_name(
                        ErdCode.UPPER_OVEN_WARMING_DRAWER_STATE,
                        not has_lower_oven,
                    ),
                )
            )
        if has_upper_probe_temperature:
            oven_entities.append(
                GeOvenErdTemperatureSensor(
                    self,
                    ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP,
                    self._single_name(
                        ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP,
                        not has_lower_oven,
                    ),
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )

        if oven_config and oven_config.has_warming_drawer and warm_drawer is not None:
            oven_entities.append(
                GeErdSensor(
                    self,
                    ErdCode.WARMING_DRAWER_STATE,
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )

        # Cavity diagnostics
        oven_entities.extend(
            self._build_cavity_diagnostics(UPPER_OVEN, not has_lower_oven)
        )
        if has_lower_oven:
            oven_entities.extend(self._build_cavity_diagnostics(LOWER_OVEN, False))

        # Appliance setting entities (control lock, sound level, end tone, clock, mode limits)
        setting_entities = self._build_setting_entities()

        cooktop_entities = build_cooktop_entities(self)

        return base_entities + oven_entities + setting_entities + cooktop_entities

    def _build_cavity_diagnostics(self, oven_select: str, make_single: bool) -> List[Entity]:
        """Sensors for ERDs reported per cavity (delay time, elapsed time, probe present)."""
        entities: List[Entity] = []

        delay_erd = ErdCode[f"{oven_select}_DELAY_TIME_REMAINING"]
        if self.has_erd_code(delay_erd):
            entities.append(
                GeErdSensor(
                    self,
                    delay_erd,
                    self._single_name(delay_erd, make_single),
                    suggested_uom="h",
                )
            )

        elapsed_erd = ErdCode[f"{oven_select}_ELAPSED_COOK_TIME"]
        if self.has_erd_code(elapsed_erd):
            entities.append(
                GeErdSensor(
                    self,
                    elapsed_erd,
                    self._single_name(elapsed_erd, make_single),
                    suggested_uom="h",
                )
            )

        probe_erd = ErdCode[f"{oven_select}_PROBE_PRESENT"]
        if self.has_erd_code(probe_erd):
            entities.append(
                GeErdBinarySensor(
                    self,
                    probe_erd,
                    self._single_name(probe_erd, make_single),
                    icon_on_override="mdi:thermometer-check",
                    icon_off_override="mdi:thermometer-off",
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )

        return entities

    def _build_setting_entities(self) -> List[Entity]:
        """Appliance-level configuration ERDs (control lock, tones, clock, mode limits)."""
        entities: List[Entity] = []

        if self.has_erd_code(ErdCode.USER_INTERFACE_LOCKED):
            entities.append(
                GeErdSwitch(
                    self,
                    ErdCode.USER_INTERFACE_LOCKED,
                    erd_override="CONTROL_LOCK",
                    icon_on_override="mdi:lock",
                    icon_off_override="mdi:lock-open-variant",
                    entity_category=EntityCategory.CONFIG,
                )
            )
        if self.has_erd_code(ErdCode.HOUR_12_SHUTOFF_ENABLED):
            entities.append(
                GeErdSwitch(
                    self,
                    ErdCode.HOUR_12_SHUTOFF_ENABLED,
                    icon_on_override="mdi:timer-off-outline",
                    icon_off_override="mdi:timer-outline",
                    entity_category=EntityCategory.CONFIG,
                )
            )
        if self.has_erd_code(ErdCode.CONVECTION_CONVERSION):
            entities.append(
                GeErdSwitch(
                    self,
                    ErdCode.CONVECTION_CONVERSION,
                    icon_on_override="mdi:autorenew",
                    icon_off_override="mdi:autorenew-off",
                    entity_category=EntityCategory.CONFIG,
                )
            )
        if self.has_erd_code(ErdCode.SOUND_LEVEL):
            entities.append(
                GeErdSelect(
                    self,
                    ErdCode.SOUND_LEVEL,
                    SoundLevelOptionsConverter(),
                    icon_override="mdi:volume-high",
                    entity_category=EntityCategory.CONFIG,
                )
            )
        if self.has_erd_code(ErdCode.END_TONE):
            entities.append(
                GeErdSelect(
                    self,
                    ErdCode.END_TONE,
                    EndToneOptionsConverter(),
                    icon_override="mdi:bell-ring-outline",
                    entity_category=EntityCategory.CONFIG,
                )
            )
        if self.has_erd_code(ErdCode.CLOCK_FORMAT):
            entities.append(
                GeErdSelect(
                    self,
                    ErdCode.CLOCK_FORMAT,
                    ClockFormatOptionsConverter(),
                    icon_override="mdi:clock-outline",
                    entity_category=EntityCategory.CONFIG,
                )
            )
        if self.has_erd_code(ErdCode.OVEN_MODE_MIN_MAX_TEMP):
            entities.extend(
                [
                    GeErdPropertySensor(
                        self,
                        ErdCode.OVEN_MODE_MIN_MAX_TEMP,
                        "lower",
                        erd_override="oven_mode_min_temp",
                        icon_override="mdi:thermometer-low",
                        device_class_override=SensorDeviceClass.TEMPERATURE,
                        data_type_override=ErdDataType.INT,
                        uom_override=UnitOfTemperature.FAHRENHEIT,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    GeErdPropertySensor(
                        self,
                        ErdCode.OVEN_MODE_MIN_MAX_TEMP,
                        "upper",
                        erd_override="oven_mode_max_temp",
                        icon_override="mdi:thermometer-high",
                        device_class_override=SensorDeviceClass.TEMPERATURE,
                        data_type_override=ErdDataType.INT,
                        uom_override=UnitOfTemperature.FAHRENHEIT,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                ]
            )

        return entities

    def _single_name(self, erd_code: ErdCode, make_single: bool):
        name = erd_code.name

        if make_single:
            name = name.replace(UPPER_OVEN + "_", "")

        return name.replace("_", " ").title()

    def _temperature_code(self, has_raw: bool):
        return "RAW_TEMPERATURE" if has_raw else "DISPLAY_TEMPERATURE"

    def _has_oven_control_erds(self, oven_select: str) -> bool:
        return (
            self.has_erd_code(ErdCode[f"{oven_select}_AVAILABLE_COOK_MODES"])
            and self.has_erd_code(ErdCode[f"{oven_select}_COOK_MODE"])
            and self.has_erd_code(ErdCode[f"{oven_select}_DISPLAY_TEMPERATURE"])
            and self.has_erd_code(ErdCode.OVEN_MODE_MIN_MAX_TEMP)
        )
