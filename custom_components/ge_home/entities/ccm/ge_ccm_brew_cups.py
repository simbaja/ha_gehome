from homeassistant.const import EntityCategory
from homeassistant.components.number import NumberMode
from gehomesdk import ErdCode

from ...devices import ApplianceApi
from ..common import GeErdNumber
from .ge_ccm_cached_value import GeCcmCachedValue

class GeCcmBrewCupsNumber(GeErdNumber, GeCcmCachedValue):
    def __init__(self, api: ApplianceApi):
        GeErdNumber.__init__(self, api = api, erd_code = ErdCode.CCM_BREW_CUPS, min_value=1, max_value=10, mode=NumberMode.BOX, entity_category=EntityCategory.DIAGNOSTIC)
        GeCcmCachedValue.__init__(self)

        self._set_value = None

    async def async_set_native_value(self, value):
        GeCcmCachedValue.set_value(self, value)
        self.schedule_update_ha_state()

    @property
    def native_value(self) -> int: # type: ignore
        return int(self.get_value(device_value = super().native_value) or 0.0)
