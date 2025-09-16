import logging
from homeassistant.components.fan import FanEntity, FanEntityFeature

_LOGGER = logging.getLogger(__name__)

# Mapping raw Haier fan levels → HA percentages
FAN_SPEED_MAP = {
    0: "off",
    1: "low",
    2: "medium",
    3: "high",
    4: "boost",
}

class GeHaierHoodFan(FanEntity):
    """Fan control for Haier FPA range hoods."""

    def __init__(self, api, erd_code):
        self._api = api
        self._appliance = api.appliance
        self._erd_code = erd_code
        self._attr_supported_features = FanEntityFeature.SET_SPEED
        self._attr_name = f"{self._appliance.mac_addr} Hood Fan"
        self._attr_unique_id = f"{self._appliance.mac_addr}_{erd_code}"

    @property
    def available(self):
        return self._appliance.has_erd_code(self._erd_code)

    @property
    def is_on(self):
        return self.fan_speed != "off"

    @property
    def percentage(self):
        raw_val = self._appliance.get_erd_value(self._erd_code) or 0
        if raw_val == 0:
            return 0
        # Map evenly across 4 steps (25, 50, 75, 100)
        return raw_val * 25

    @property
    def speed_count(self):
        return len(FAN_SPEED_MAP)

    @property
    def fan_speed(self):
        raw_val = self._appliance.get_erd_value(self._erd_code) or 0
        return FAN_SPEED_MAP.get(raw_val, "off")

    async def async_set_percentage(self, percentage: int):
        raw_val = round(percentage / 25)
        _LOGGER.debug(f"Setting hood fan to {raw_val} for {self._appliance.mac_addr}")
        await self._appliance.async_set_erd_value(self._erd_code, raw_val)

    async def async_turn_on(self, percentage: int | None = None, **kwargs):
        if percentage is None:
            percentage = 25
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs):
        await self._appliance.async_set_erd_value(self._erd_code, 0)
