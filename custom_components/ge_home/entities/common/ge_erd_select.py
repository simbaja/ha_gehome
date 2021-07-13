
import logging
from typing import Any, List

from homeassistant.components.select import SelectEntity
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from .ge_erd_entity import GeErdEntity

_LOGGER = logging.getLogger(__name__)

class OptionsConverter:
    @property
    def options(self) -> List[str]:
        return []
    def from_option_string(self, value: str) -> Any:
        return value
  
class GeErdSelect(GeErdEntity, SelectEntity):
    """ERD-based selector entity"""
    device_class = "select"

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, converter: OptionsConverter, erd_override: str = None, icon_override: str = None, device_class_override: str = None):
        super().__init__(api, erd_code, erd_override=erd_override, icon_override=icon_override, device_class_override=device_class_override)
        self._converter = converter

    def options(self) -> List[str]:
        "Return a list of options"
        return self._converter.options
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option != self.current_option:
            await self.appliance.async_set_erd_value(self.erd_code, self._converter.from_option_string(option))