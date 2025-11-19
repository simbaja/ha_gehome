"""GE Home Sensor Entities - Freezer"""
import logging
from typing import Any, Dict

from gehomesdk import (
    ErdCode,
    ErdCodeType,
    ErdDoorStatus
)

from .ge_abstract_fridge import (
    ATTR_DOOR_STATUS, 
    HEATER_TYPE_FREEZER, 
    OP_MODE_TURBO_FREEZE,
    GeAbstractFridge
)

_LOGGER = logging.getLogger(__name__)

class GeFreezer(GeAbstractFridge):
    """A freezer is basically a fridge."""

    @property
    def heater_type(self) -> str:
        return HEATER_TYPE_FREEZER
    
    @property
    def icon(self) -> str | None:
        return "mdi:fridge-top"   
    
    @property
    def turbo_erd_code(self) -> ErdCodeType:
        return ErdCode.TURBO_FREEZE_STATUS

    @property
    def turbo_mode(self) -> str:
        return OP_MODE_TURBO_FREEZE  

    @property
    def door_state_attrs(self) -> Dict[str, Any]:
        try:
            door_status = self.door_status.freezer
            if door_status and door_status != ErdDoorStatus.NA:
                return {ATTR_DOOR_STATUS: self._stringify(door_status)}
        except:
            _LOGGER.debug("Device does not report door status.")
        return {}
