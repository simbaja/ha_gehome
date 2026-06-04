"""GE Home Sensor Entities - Oven"""
from homeassistant.const import UnitOfTemperature
from gehomesdk import ErdMeasurementUnits

from ..common import GeErdSensor


class GeOvenErdTemperatureSensor(GeErdSensor):
    """Oven temperature sensor that honours a metric Fisher & Paykel oven's unit.

    ``GeErdSensor`` hard-codes Fahrenheit for temperature sensors because GE
    appliances always report Fahrenheit regardless of the configured locale
    (and may even report a ``METRIC`` unit while still sending Fahrenheit, see
    simbaja/gehome#21).  Fisher & Paykel ovens sold in metric markets are the
    documented exception: their raw ERD temperatures are already Celsius, so
    Home Assistant must not re-convert them.  We therefore trust the device's
    measurement system only for F&P-branded ovens, leaving every GE appliance
    on the historical Fahrenheit behaviour.
    """

    def _get_uom(self):
        uom = super()._get_uom()

        # super() returns Fahrenheit only for temperature sensors; flip those to
        # Celsius only for a metric F&P oven, whose raw values are Celsius.
        if (
            uom == UnitOfTemperature.FAHRENHEIT
            and not self._uom_override
            and self.api.is_fisher_paykel
            and self._measurement_system == ErdMeasurementUnits.METRIC
        ):
            return UnitOfTemperature.CELSIUS
        return uom
