import logging
from propcache.api import cached_property
from typing import Optional

from homeassistant.const import EntityCategory
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from .ge_erd_binary_sensor import GeErdEntity
from .bool_converter import BoolConverter

_LOGGER = logging.getLogger(__name__)

class GeErdSwitch(GeErdEntity, SwitchEntity):
    """Switches for boolean ERD codes."""

    def __init__(
            self, 
            api: ApplianceApi, 
            erd_code: ErdCodeType, 
            bool_converter: BoolConverter = BoolConverter(), 
            erd_override: Optional[str] = None, 
            icon_on_override: Optional[str] = None, 
            icon_off_override: Optional[str] = None, 
            device_class_override: Optional[str] = None,
            control_erd_code: Optional[ErdCodeType] = None,
            entity_category: Optional[EntityCategory] = None
        ):
        super().__init__(api, erd_code, erd_override, icon_on_override, device_class_override, entity_category)
        self._icon_on_override = icon_on_override
        self._icon_off_override = icon_off_override
        self._converter = bool_converter
        self._control_erd_code = control_erd_code

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available

    @property
    def is_on(self) -> bool: # type: ignore
        """Return True if switch is on."""
        return self._converter.boolify(self.appliance.get_erd_value(self.erd_code))
    
    @cached_property
    def device_class(self) -> SwitchDeviceClass | None:       
        dc = self._get_device_class()

        if dc is None:
            return None
    
        if isinstance(dc, str):
            try:
                return SwitchDeviceClass(dc)
            except ValueError:
                return None
        if isinstance(dc, SwitchDeviceClass):
            return dc

        return None
    
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.debug(f"Turning on {self.unique_id}")

        await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.true_value())

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        _LOGGER.debug(f"Turning off {self.unique_id}")
        await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.false_value())

    def _get_icon(self):
        if self._icon_on_override and self.is_on:
            return self._icon_on_override
        if self._icon_off_override and not self.is_on:
            return self._icon_off_override

        return super()._get_icon()

    def _get_device_class(self) -> Optional[str]:
        if self._device_class_override:
            return self._device_class_override
        return None
    
    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        if self._control_erd_code:
            return self._control_erd_code
        
        return self.erd_code
