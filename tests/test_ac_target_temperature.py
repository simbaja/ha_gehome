"""AC target temperature read as 16896 instead of 66 .

Some AC units report ERD 0x7003 as the 2-byte payload "4200". gehomesdk decodes
0x7003 with int(value, 16) (big endian), so "4200" becomes 16896 (= 66 * 256) on both
the diagnostic sensor and the climate's `temperature` attribute, while other reports of
the same setpoint ("42" / "0042") decode to 66. Normalize the setpoint in either byte order.
"""

import pytest
from gehomesdk import ErdCode, GeAppliance

from custom_components.ge_home.entities.ac.target_temperature import (
    GeAcTargetTemperatureSensor,
    normalize_ac_target_temperature,
)
from custom_components.ge_home.entities.common.ge_climate import GeClimate
from custom_components.ge_home.entities.common.options_converter import OptionsConverter

MAC = "AABBCCDDEEFF"
REAL_RAW_FROM_THE_CLOUD = "4200"  # '0x7003' in the 2026-11-18 07:24 allErd response from an AC unit


class _Client:
    """Only what GeAppliance reads from its client."""

    client_priority = 0


class _Api:
    """The slice of ApplianceApi the two entities read."""

    def __init__(self, appliance):
        self.appliance = appliance
        self.entity_identifier = "GarageAC"
        self.available = True
        self.mac_addr = MAC
        self.serial_or_mac = MAC
        self.device_info = None

    def try_get_erd_value(self, erd_code):
        try:
            return self.appliance.get_erd_value(erd_code)
        except KeyError:
            return None


class _Options(OptionsConverter):
    @property
    def options(self):
        return []

    def from_option_string(self, value):
        return value

    def to_option_string(self, value):
        return value


# The rest of the AC allErd response that the climate reads (raw, as the cloud sent it).
REAL_REST_OF_THE_RESPONSE = {
    "0x0007": "00",  # temperature unit: imperial
    "0x7A00": "02",  # operation mode
    "0x7A01": "02",  # fan setting
    "0x7A02": "32",  # ambient temperature = 50 F, one byte
    "0x7A0F": "00",  # power status: off
}


def _api_with_raw(raw: str) -> _Api:
    appliance = GeAppliance(MAC, _Client())
    appliance.update_erd_values({**REAL_REST_OF_THE_RESPONSE, "0x7003": raw})
    return _Api(appliance)


def test_sdk_reads_the_real_raw_value_unscaled():
    """Precondition: the SDK itself hands the integration 16896 for the real payload."""
    api = _api_with_raw(REAL_RAW_FROM_THE_CLOUD)
    assert api.appliance.get_erd_value(ErdCode.AC_TARGET_TEMPERATURE) == 66 * 256


def test_sensor_reports_66_for_the_real_raw_value():
    sensor = GeAcTargetTemperatureSensor(_api_with_raw(REAL_RAW_FROM_THE_CLOUD), ErdCode.AC_TARGET_TEMPERATURE)
    assert sensor.native_value == 66


@pytest.mark.parametrize("raw", ["42", "0042"])
def test_sensor_keeps_66_for_the_earlier_payloads(raw):
    sensor = GeAcTargetTemperatureSensor(_api_with_raw(raw), ErdCode.AC_TARGET_TEMPERATURE)
    assert sensor.native_value == 66


def test_sensor_keeps_its_entity_identity():
    """Same unique_id and name as the plain ERD sensor it replaces: no new entity, no rename."""
    sensor = GeAcTargetTemperatureSensor(_api_with_raw(REAL_RAW_FROM_THE_CLOUD), ErdCode.AC_TARGET_TEMPERATURE)
    assert sensor.unique_id == "ge_home_GarageAC_ac_target_temperature"
    assert sensor.name == "GarageAC Ac Target Temperature"


def test_climate_target_temperature_is_66_for_the_real_raw_value():
    climate = GeClimate(_api_with_raw(REAL_RAW_FROM_THE_CLOUD), _Options(), _Options())
    assert climate.target_temperature == 66.0


@pytest.mark.parametrize("raw", ["42", "0042"])
def test_climate_target_temperature_keeps_66_for_the_earlier_payloads(raw):
    climate = GeClimate(_api_with_raw(raw), _Options(), _Options())
    assert climate.target_temperature == 66.0


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (66, 66),
        (86, 86),
        (64, 64),
        (66 * 256, 66),
        (64 * 256, 64),
        (86 * 256, 86),
        (None, None),
        # not a byte-swapped temperature: left exactly as the SDK read it
        (0, 0),
        (300, 300),
        (0x0102, 0x0102),
        (-1, -1),
    ],
)
def test_normalize(value, expected):
    assert normalize_ac_target_temperature(value) == expected
