"""GE Home Sensor Entities - Oven"""
from homeassistant.const import UnitOfTemperature

from ..common import GeErdSensor


class GeOvenErdTemperatureSensor(GeErdSensor):
    """Oven cavity temperature sensor that treats 0 as "no reading".

    The oven cavity temperature ERDs (display, raw, probe) use 0 as a
    "no reading" sentinel: a raw-temperature ERD an appliance advertises but
    never populates, or a display/probe temperature while the oven is idle.
    Surfacing the 0 would convert 0F to -17.8C, so we report it as unknown
    instead.

    This is deliberately NOT used for USER_TEMP_OFFSET, where 0 is a
    legitimate value (no offset); see GeOvenErdTemperatureOffsetSensor.
    """

    @property
    def native_value(self):  # type: ignore
        value = super().native_value
        # 0 (or None) means the appliance isn't reporting a reading.
        if not value:
            return None
        return value


class GeOvenErdTemperatureOffsetSensor(GeErdSensor):
    """Oven user temperature-offset sensor.

    USER_TEMP_OFFSET is a calibration *difference*, not an absolute
    temperature, so it must be converted as a delta (no 32-degree term):
    Home Assistant's temperature device-class conversion would otherwise turn
    a raw 0F into -17.8C, and a real +9F offset into -12.8C instead of +5C.

    The appliance transmits the offset in Fahrenheit (like every other oven
    temperature ERD), so we convert the raw Fahrenheit delta to the user's
    configured unit ourselves and report it natively in that unit, leaving
    Home Assistant nothing to re-convert.
    """

    @property
    def native_value(self):  # type: ignore
        value = self.appliance.get_erd_value(self.erd_code)
        if value is None:
            return None
        # Raw value is a Fahrenheit difference; convert as a delta.
        if self._temp_units == UnitOfTemperature.CELSIUS:
            return round(value * 5 / 9, 1)
        return value

    @property
    def native_unit_of_measurement(self):  # type: ignore
        # native_value is already in the display unit, so report that unit to
        # stop HA applying a second (absolute) temperature conversion.
        return self._temp_units


class GeOvenErdCookModeSensor(GeErdSensor):
    """Cook-mode sensor that converts the embedded setpoint to the display unit.

    The cook-mode ERD decodes to an OvenCookSetting whose temperature is in
    Fahrenheit (like all oven temperatures). Its stringify() embeds that raw
    number with a unit label but does not convert it, so a metric user sees
    e.g. "Bake (356C)" for a 180C setpoint. Convert the embedded temperature
    to the user's unit before stringifying.
    """

    @property
    def native_value(self):  # type: ignore
        try:
            value = self.appliance.get_erd_value(self.erd_code)
        except (KeyError, ValueError):
            return None
        if value is None:
            return None
        temp_units = self._temp_units
        temperature = getattr(value, "temperature", 0)
        # Raw setpoint is Fahrenheit; convert as an absolute temperature so the
        # metric label matches the value ("Bake (180C)", not "Bake (356C)").
        if temperature and temp_units == UnitOfTemperature.CELSIUS:
            value = value._replace(temperature=round((temperature - 32) * 5 / 9))
        return self._stringify(value, temp_units=temp_units)
