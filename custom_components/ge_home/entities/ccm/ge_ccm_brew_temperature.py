from homeassistant.const import EntityCategory
from homeassistant.components.number import NumberMode
from gehomesdk import ErdCode

from ...devices import ApplianceApi
from ..common import GeErdNumber
from .ge_ccm_cached_value import GeCcmCachedValue

DEFAULT_MIN_TEMP = 100
DEFAULT_MAX_TEMP = 225

class GeCcmBrewTemperatureNumber(GeErdNumber, GeCcmCachedValue):
    def __init__(self, api: ApplianceApi):
        try:
            min_temp, max_temp, _ = api.appliance.get_erd_value(ErdCode.CCM_BREW_TEMPERATURE_RANGE)
        except:
            min_temp = DEFAULT_MIN_TEMP
            max_temp = DEFAULT_MAX_TEMP
 
        GeErdNumber.__init__(self, api = api, erd_code = ErdCode.CCM_BREW_TEMPERATURE, min_value=min_temp, max_value=max_temp, mode=NumberMode.SLIDER, entity_category=EntityCategory.DIAGNOSTIC)
        GeCcmCachedValue.__init__(self)

    async def async_set_native_value(self, value):
        GeCcmCachedValue.set_value(self, value)
        self.schedule_update_ha_state()

    @property
    def native_value(self) -> int: # type: ignore
        return int(self.get_value(device_value = super().native_value) or self.min_value)
