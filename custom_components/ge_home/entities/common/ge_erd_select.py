
import logging
from propcache.api import cached_property
from typing import Any, List, Optional

from homeassistant.const import EntityCategory
from homeassistant.components.select import SelectEntity
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from .ge_erd_entity import GeErdEntity
from .options_converter import OptionsConverter

_LOGGER = logging.getLogger(__name__)
  
class GeErdSelect(GeErdEntity, SelectEntity):
    """ERD-based selector entity"""

    def __init__(
            self, 
            api: ApplianceApi, 
            erd_code: ErdCodeType, 
            converter: OptionsConverter, 
            erd_override: Optional[str] = None, 
            icon_override: Optional[str] = None,
            control_erd_code: Optional[ErdCodeType] = None,
            entity_category: Optional[EntityCategory] = None
        ):
        super().__init__(api, erd_code, erd_override=erd_override, icon_override=icon_override, entity_category=entity_category)
        self._converter = converter
        self._control_erd_code = control_erd_code

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available

    @property
    def current_option(self) -> str | None: # type: ignore
        return self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))

    @cached_property
    def options(self) -> List[str]:
        "Return a list of options"
        return self._converter.options
    
    async def async_select_option(self, option: str) -> None:
        _LOGGER.debug(f"Setting select from {self.current_option} to {option}")
        """Change the selected option."""
        if option != self.current_option:
            await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.from_option_string(option))

    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        if self._control_erd_code:
            return self._control_erd_code
        
        return self.erd_code