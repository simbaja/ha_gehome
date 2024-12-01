import logging
from typing import List, Any, Optional

from gehomesdk import ErdCode, ErdCcmBrewStrength
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter
from .ge_ccm_cached_value import GeCcmCachedValue

_LOGGER = logging.getLogger(__name__)

class GeCcmBrewStrengthOptionsConverter(OptionsConverter):
    def __init__(self):
        self._default = ErdCcmBrewStrength.MEDIUM

    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in [ErdCcmBrewStrength.LIGHT, ErdCcmBrewStrength.MEDIUM, ErdCcmBrewStrength.BOLD, ErdCcmBrewStrength.GOLD]]

    def from_option_string(self, value: str) -> Any:
        try:
            return ErdCcmBrewStrength[value.upper()]
        except:
            _LOGGER.warning(f"Could not set brew strength to {value.upper()}")
            return self._default

    def to_option_string(self, value: ErdCcmBrewStrength) -> Optional[str]:
        try:
            return value.stringify()
        except:
            return self._default.stringify()

class GeCcmBrewStrengthSelect(GeErdSelect, GeCcmCachedValue):
    def __init__(self, api: ApplianceApi):
        GeErdSelect.__init__(self, api = api, erd_code = ErdCode.CCM_BREW_STRENGTH, converter = GeCcmBrewStrengthOptionsConverter())
        GeCcmCachedValue.__init__(self)

    @property
    def brew_strength(self) -> ErdCcmBrewStrength:
        return self._converter.from_option_string(self.current_option)

    async def async_select_option(self, value):
        GeCcmCachedValue.set_value(self, value)
        self.schedule_update_ha_state()

    @property
    def current_option(self):
        return self.get_value(device_value = super().current_option)