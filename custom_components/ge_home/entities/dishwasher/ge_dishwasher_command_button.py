from propcache.api import cached_property
from typing import Optional

from gehomesdk import ErdCode, ErdRemoteCommand
from ...devices import ApplianceApi
from ..common import GeErdButton

class GeDishwasherCommandButton(GeErdButton):
    def __init__(self, api: ApplianceApi, erd_code: ErdCode, command: ErdRemoteCommand, erd_override: Optional[str] = None):
        super().__init__(api, erd_code=erd_code, erd_override=erd_override)
        self._command = command
        self._command_cleansed = self._command.name.replace(".","_").replace("[","_").replace("]","_")

    @cached_property
    def unique_id(self) -> str | None:
        return f"{super().unique_id}_{self._command_cleansed}"

    @cached_property
    def name(self) -> Optional[str]:
        base_string = super().name
        property_name = self._command_cleansed.replace("_", " ").title()
        return f"{base_string} {property_name}"
    
    async def async_press(self) -> None:
        """Handle the button press."""
        await self.appliance.async_set_erd_value(self.erd_code, self._command)

    def _get_icon(self) -> Optional[str]:
        return {
            ErdRemoteCommand.START_RESUME: "mdi:play",
            ErdRemoteCommand.CANCEL: "mdi:stop",
            ErdRemoteCommand.PAUSE: "mdi:pause"
        }.get(self._command)