import logging
from homeassistant.components.light import LightEntity, ColorMode

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodLight(LightEntity):
    """Light control for Haier FPA range hoods."""

    def __init__(self, api, erd_code):
        self._api = api
        self._appliance = api.appliance
        self._erd_code = erd_code
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
        self._attr_name = f"{self._appliance.mac_addr} Hood Light"
        self._attr_unique_id = f"{self._appliance.mac_addr}_{erd_code}"

    @property
    def available(self):
        return self._appliance.has_erd_code(self._erd_code)

    @property
    def is_on(self):
        val = self._appliance.get_erd_value(self._erd_code) or 0
        return val == 1

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug(f"Turning on hood light for {self._appliance.mac_addr}")
        await self._appliance.async_set_erd_value(self._erd_code, 1)

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug(f"Turning off hood light for {self._appliance.mac_addr}")
        await self._appliance.async_set_erd_value(self._erd_code, 0)
