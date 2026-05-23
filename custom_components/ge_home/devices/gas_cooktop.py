"""GAS_COOKTOP (ErdApplianceType.GAS_COOKTOP = "0D") support.

Standalone gas cooktops use a DEVICE_GATEWAY_V1_BLE_ADVERTISE_ONLY_SENSOR
feature flag, meaning they report via a nearby BLE-to-cloud gateway rather
than native WiFi. In practice they implement a reduced ERD surface — no
per-burner detail, no COOKTOP_STATUS_EXT — and reuse familiar hex codes
with different byte semantics.

ERDs used here were reverse-engineered from a live Monogram ZGU36ESLSS
by toggling each feature in the SmartHQ app and diffing publish#erd
events:

  0x5520 - byte 0: cooktop-on aggregate
           00 = all burners off, 01 = any burner on
           (remaining 11 bytes all 0xFF - per-burner detail unused)
  0x5900 - lock state enum
           01 = unlocked, 02 = transitioning, 03 = locked
  0x5105 - kitchen timer minutes remaining (uint16 big-endian)
           0000 = idle, NNNN = minutes remaining; writable 0-599
  0x5020 - byte 0: timer alarm
           01 = beeping, 00 = quiet (auto-clears when user taps ack)
  0x5902 - cooking minutes (uint16 big-endian)
           increments once per minute while any burner is on,
           resets to 0 when all burners turn off

Three of these (0x5020, 0x5105, 0x5520) are registered in gehomesdk's
ErdCode enum under different names (HOOD_TIMER, UPPER_OVEN_KITCHEN_TIMER,
COOKTOP_STATUS) whose converters decode into oven/hood-shaped objects
meaningless on this appliance. We read their raw bytes via
``appliance.get_raw_erd_value()`` and decode per the gas-cooktop schema.

The writable kitchen timer (0x5105) bypasses the SDK encoder registry
for the same reason — UPPER_OVEN_KITCHEN_TIMER's upstream encoder
expects a ``timedelta`` in seconds, but the gas cooktop takes raw
big-endian minutes. We call ``appliance.client.async_set_erd_value()``
directly with a hand-encoded 2-byte hex string.

Writes to the lock ERD (0x5900) are rejected by the Brillion server
with ``400 "erd is not writable"`` even though the SmartHQ app can
successfully lock. The server enforces per-OAuth-client-id writability
for safety-sensitive ERDs; the SDK's client_id is not whitelisted.
Lock is therefore exposed as a read-only BinarySensor.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberMode
from homeassistant.components.sensor import SensorStateClass
from homeassistant.helpers.entity import Entity

from gehomesdk import ErdApplianceType

from .base import ApplianceApi
from ..entities import GeErdBinarySensor, GeErdNumber, GeErdSensor

_LOGGER = logging.getLogger(__name__)


# Raw ERD codes — strings because several of these collide with upstream
# ErdCode members whose converters produce oven/hood-shaped objects. We
# sidestep the converters entirely by reading raw bytes.
ERD_COOKTOP_ON = "0x5520"
ERD_LOCK = "0x5900"
ERD_TIMER_MINUTES = "0x5105"
ERD_TIMER_ALARM = "0x5020"
ERD_COOKING_MINUTES = "0x5902"

_LOCK_UNLOCKED = 0x01


def _read_bytes(appliance, erd_code: str) -> Optional[bytes]:
    """Fetch the raw bytes for an ERD, or None if not yet received."""
    raw = appliance.get_raw_erd_value(erd_code)
    if not raw:
        return None
    try:
        return bytes.fromhex(raw)
    except ValueError:
        return None


def _first_byte(appliance, erd_code: str) -> Optional[int]:
    b = _read_bytes(appliance, erd_code)
    return b[0] if b else None


def _uint_be(appliance, erd_code: str, nbytes: int) -> Optional[int]:
    b = _read_bytes(appliance, erd_code)
    if not b or len(b) < nbytes:
        return None
    return int.from_bytes(b[:nbytes], "big")


class _GasCooktopBinaryBase(GeErdBinarySensor):
    """Base that returns just the label as name — HA prepends the device
    name automatically, so the entity displays as e.g. 'Monogram Gas
    Cooktop 0200002A410E Locked'."""

    _label: str = ""

    @property
    def name(self) -> str:
        return self._label


class _GasCooktopSensorBase(GeErdSensor):
    _label: str = ""

    @property
    def name(self) -> str:
        return self._label


class GasCooktopOnSensor(_GasCooktopBinaryBase):
    _label = "Cooktop On"
    _raw_erd = ERD_COOKTOP_ON

    def __init__(self, api: ApplianceApi) -> None:
        super().__init__(
            api,
            ERD_COOKTOP_ON,
            device_class_override=BinarySensorDeviceClass.POWER,
        )

    @property
    def is_on(self) -> Optional[bool]:
        b = _first_byte(self.appliance, self._raw_erd)
        return None if b is None else b == 0x01


class GasCooktopLockedSensor(_GasCooktopBinaryBase):
    _label = "Locked"
    _raw_erd = ERD_LOCK

    def __init__(self, api: ApplianceApi) -> None:
        super().__init__(
            api,
            ERD_LOCK,
            device_class_override=BinarySensorDeviceClass.LOCK,
        )

    @property
    def is_on(self) -> Optional[bool]:
        # BinarySensorDeviceClass.LOCK convention: on=unlocked, off=locked.
        b = _first_byte(self.appliance, self._raw_erd)
        if b is None:
            return None
        return b == _LOCK_UNLOCKED


class GasCooktopTimerAlarmSensor(_GasCooktopBinaryBase):
    _label = "Kitchen Timer Alarm"
    _raw_erd = ERD_TIMER_ALARM

    def __init__(self, api: ApplianceApi) -> None:
        super().__init__(
            api,
            ERD_TIMER_ALARM,
            icon_on_override="mdi:alarm-bell",
            icon_off_override="mdi:alarm-bell-outline",
            device_class_override=BinarySensorDeviceClass.SOUND,
        )

    @property
    def is_on(self) -> Optional[bool]:
        b = _first_byte(self.appliance, self._raw_erd)
        return None if b is None else b == 0x01


class GasCooktopKitchenTimerNumber(GeErdNumber):
    """Kitchen timer — writable 0-599 minutes (empirical device ceiling;
    SmartHQ's UI advertises 10h59m but the cooktop rejects writes > 599).

    Reads bypass the SDK registry via get_raw_erd_value(); writes bypass
    the SDK encoder (UPPER_OVEN_KITCHEN_TIMER's encoder expects timedelta
    seconds, but the gas cooktop takes raw big-endian minutes).
    """

    _label = "Kitchen Timer"
    _raw_erd = ERD_TIMER_MINUTES
    _max_minutes = 599

    def __init__(self, api: ApplianceApi) -> None:
        super().__init__(
            api,
            ERD_TIMER_MINUTES,
            icon_override="mdi:timer-outline",
            uom_override="min",
            min_value=0,
            max_value=float(self._max_minutes),
            step_value=1,
            mode=NumberMode.BOX,
        )

    @property
    def name(self) -> str:
        return self._label

    @property
    def device_class(self) -> None:
        # Avoid DURATION auto-conversion (min -> seconds in the UI).
        return None

    @property
    def native_value(self) -> Optional[float]:
        val = _uint_be(self.appliance, self._raw_erd, 2)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        minutes = max(0, min(self._max_minutes, int(round(value))))
        hex_value = f"{minutes:04X}"
        await self.appliance.client.async_set_erd_value(
            self.appliance, self._raw_erd, hex_value
        )


class GasCooktopCookingMinutesSensor(_GasCooktopSensorBase):
    """Minutes the cooktop has been actively cooking.

    Ticks up once per minute while any burner is on and resets to 0 once
    all burners turn off. SmartHQ's 1-hour 'cooktop still on' alert fires
    when this counter hits 60.
    """

    _label = "Cooking Minutes"
    _raw_erd = ERD_COOKING_MINUTES

    def __init__(self, api: ApplianceApi) -> None:
        super().__init__(
            api,
            ERD_COOKING_MINUTES,
            icon_override="mdi:pot-steam",
            uom_override="min",
            state_class_override=SensorStateClass.TOTAL_INCREASING,
        )

    @property
    def native_value(self) -> Optional[int]:
        return _uint_be(self.appliance, self._raw_erd, 2)


class GasCooktopApi(ApplianceApi):
    """Device handler for standalone gas cooktops
    (ErdApplianceType.GAS_COOKTOP).
    """

    APPLIANCE_TYPE = ErdApplianceType.GAS_COOKTOP

    def get_all_entities(self) -> List[Entity]:
        return [
            GasCooktopOnSensor(self),
            GasCooktopLockedSensor(self),
            GasCooktopKitchenTimerNumber(self),
            GasCooktopTimerAlarmSensor(self),
            GasCooktopCookingMinutesSensor(self),
        ]
