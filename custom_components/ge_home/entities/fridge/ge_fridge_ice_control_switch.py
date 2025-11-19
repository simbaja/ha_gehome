import logging
from gehomesdk import ErdCode, IceMakerControlStatus, ErdOnOff

from ...devices import ApplianceApi
from ..common import GeErdSwitch, BoolConverter

_LOGGER = logging.getLogger(__name__)

class GeFridgeIceControlSwitch(GeErdSwitch):    
    def __init__(self, api: ApplianceApi, control_type: str):
        super().__init__(api, ErdCode.ICE_MAKER_CONTROL, BoolConverter())
        self._control_type = control_type
    
    @property
    def control_status(self) -> IceMakerControlStatus:
        return self.appliance.get_erd_value(ErdCode.ICE_MAKER_CONTROL)

    @property
    def is_on(self) -> bool:
        if self._control_type == "fridge":
            return self.control_status.status_fridge == ErdOnOff.ON
        else:
            return self.control_status.status_freezer == ErdOnOff.ON
 
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.debug(f"Turning on {self.unique_id}")

        old_status = self.control_status
        if self._control_type == "fridge":
            new_status = IceMakerControlStatus(ErdOnOff.ON, old_status.status_freezer)
        else:
            new_status = IceMakerControlStatus(old_status.status_fridge, ErdOnOff.ON)

        await self.appliance.async_set_erd_value(self.erd_code, new_status)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        _LOGGER.debug(f"Turning off {self.unique_id}")

        old_status = self.control_status
        if self._control_type == "fridge":
            new_status = IceMakerControlStatus(ErdOnOff.OFF, old_status.status_freezer)
        else:
            new_status = IceMakerControlStatus(old_status.status_fridge, ErdOnOff.OFF)

        await self.appliance.async_set_erd_value(self.erd_code, new_status)
