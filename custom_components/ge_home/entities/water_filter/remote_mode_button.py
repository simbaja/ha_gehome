import logging
from typing import Optional

from homeassistant.const import EntityCategory
from gehomesdk import ErdCode, ErdCodeType, ErdWaterFilterValveState, ErdWaterFilterManualMode

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdButton

_LOGGER = logging.getLogger(__name__)


class GeWaterFilterRemoteModeButton(GeErdButton):
    """
    Returns a POE whole-home water filter to remote mode after a manual override
    (the SmartHQ app's "Back to remote mode" action).

    The SDK's converters for these ERDs are read-only, so the raw hex value is
    sent straight to the client, bypassing the encoder.
    """

    def __init__(
        self,
        api: ApplianceApi,
        erd_code: ErdCodeType,
        raw_value: str,
        name_override: str,
        unique_suffix: str,
        icon: str = "mdi:remote",
    ):
        super().__init__(api, erd_code, erd_override=name_override, entity_category=EntityCategory.CONFIG)
        self._raw_value = raw_value
        self._unique_suffix = unique_suffix
        self._icon_override = icon

    @property
    def unique_id(self) -> Optional[str]:  # type: ignore
        return f"{DOMAIN}_{self.entity_identifier}_{self._unique_suffix}"

    @property
    def available(self) -> bool:  # type: ignore
        if not super().available:
            return False
        try:
            valve = self.appliance.get_erd_value(ErdCode.WH_FILTER_VALVE_STATE)
            manual = self.appliance.get_erd_value(ErdCode.WH_FILTER_MANUAL_MODE)
        except KeyError:
            return True
        # only offer the action while the unit is in manual override
        return (
            valve == ErdWaterFilterValveState.MANUAL_OVERRIDE
            or manual == ErdWaterFilterManualMode.MANUAL
        )

    async def async_press(self) -> None:
        _LOGGER.debug(f"Water filter remote mode: writing {self.erd_code}={self._raw_value}")
        await self.appliance.client.async_set_erd_value(self.appliance, self.erd_code, self._raw_value)
