from gehomesdk import ErdCode
from ...devices import ApplianceApi
from ..common import GeErdNumber
from .ge_ccm_cached_value import GeCcmCachedValue

class GeCcmBrewTemperatureNumber(GeErdNumber, GeCcmCachedValue):
    def __init__(self, api: ApplianceApi):
        min_temp, max_temp, _ = api.appliance.get_erd_value(ErdCode.CCM_BREW_TEMPERATURE_RANGE)
        GeErdNumber.__init__(self, api = api, erd_code = ErdCode.CCM_BREW_TEMPERATURE, min_value=min_temp, max_value=max_temp, mode="slider")
        GeCcmCachedValue.__init__(self)

    async def async_set_native_value(self, value):
        GeCcmCachedValue.set_value(self, value)
        self.schedule_update_ha_state()

    @property
    def native_value(self):
        return int(self.get_value(device_value = super().native_value))
