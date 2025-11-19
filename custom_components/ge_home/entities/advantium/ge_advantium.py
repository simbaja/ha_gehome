"""GE Home Sensor Entities - Advantium"""
import logging
from propcache.api import cached_property
from typing import Any, List, Mapping, Optional, cast
from random import randrange

from homeassistant.const import ATTR_TEMPERATURE
from gehomesdk import (
    ErdCode,
    ErdPersonality,
    ErdAdvantiumCookStatus, 
    ErdAdvantiumCookSetting, 
    AdvantiumOperationMode, 
    AdvantiumCookSetting,
    AdvantiumCookAction, 
    AdvantiumCookMode, 
    AdvantiumWarmStatus,
    ErdAdvantiumRemoteCookModeConfig,
    ADVANTIUM_OPERATION_MODE_COOK_SETTING_MAPPING     
)

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeAbstractWaterHeater
from .const import *

_LOGGER = logging.getLogger(__name__)

class GeAdvantium(GeAbstractWaterHeater):
    """GE Appliance Advantium"""

    def __init__(self, api: ApplianceApi):
        super().__init__(api)
        self._current_operation_mode = None

    @property
    def icon(self) -> Optional[str]:
        return "mdi:microwave"        

    @property
    def supported_features(self):
        if self.remote_enabled:
            return GE_ADVANTIUM_WITH_TEMPERATURE if self.can_set_temperature else GE_ADVANTIUM
        else:
            return SUPPORT_NONE

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_number}"

    @cached_property
    def name(self) -> Optional[str]:
        return f"{self.serial_number} Advantium"

    @property
    def personality(self) -> Optional[ErdPersonality]:
        try:
            return self.appliance.get_erd_value(ErdCode.PERSONALITY)
        except:
            return None

    @property
    def remote_enabled(self) -> bool:
        """Returns whether the oven is remote enabled"""
        value = self.appliance.get_erd_value(ErdCode.UPPER_OVEN_REMOTE_ENABLED)
        return value == True

    @property
    def current_temperature(self) -> int | None: # type: ignore
        return self.appliance.get_erd_value(ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE)

    @property
    def current_operation(self) -> Optional[str]: # type: ignore
        if self.current_operation_mode is None:
            return None
        
        try:
            return self.current_operation_mode.stringify()
        except:
            return None

    @cached_property
    def operation_list(self) -> List[str]:
        invalid = []
        if not self._remote_config.broil_enable:
            invalid.append(AdvantiumCookMode.BROIL)
        if not self._remote_config.convection_bake_enable:
            invalid.append(AdvantiumCookMode.CONVECTION_BAKE)
        if not self._remote_config.proof_enable:
            invalid.append(AdvantiumCookMode.PROOF)
        if not self._remote_config.warm_enable:
            invalid.append(AdvantiumCookMode.WARM)

        return [
            k.stringify()
            for k, v in ADVANTIUM_OPERATION_MODE_COOK_SETTING_MAPPING.items() 
            if v.cook_mode not in invalid]

    @property
    def current_cook_setting(self) -> ErdAdvantiumCookSetting:
        """Get the current cook setting."""
        return cast(ErdAdvantiumCookSetting, self.appliance.get_erd_value(ErdCode.ADVANTIUM_COOK_SETTING))

    @property
    def current_cook_status(self) -> ErdAdvantiumCookStatus:
        """Get the current status."""
        return cast(ErdAdvantiumCookStatus, self.appliance.get_erd_value(ErdCode.ADVANTIUM_COOK_STATUS))

    @property
    def current_operation_mode(self) -> AdvantiumOperationMode | None:
        """Gets the current operation mode"""
        self._ensure_operation_mode()
        return self._current_operation_mode

    @property
    def current_operation_setting(self) -> Optional[AdvantiumCookSetting]:
        if self.current_operation_mode is None:
            return None
        try:
            return ADVANTIUM_OPERATION_MODE_COOK_SETTING_MAPPING[self.current_operation_mode]
        except:
            _LOGGER.warning(f"Unable to determine operation setting, mode = {self.current_operation_mode}")
            return None
            
    @property
    def can_set_temperature(self) -> bool:
        """Indicates whether we can set the temperature based on the current mode"""
        
        if self.current_operation_setting is None:
            return False       
        try:           
            return self.current_operation_setting.allow_temperature_set
        except:
            return False

    @property
    def target_temperature(self) -> int | None: # type: ignore
        """Return the temperature we try to reach."""
        try:
            cook_mode = self.current_cook_setting
            if (
                cook_mode.cook_mode != AdvantiumCookMode.NO_MODE and 
                cook_mode.target_temperature and 
                cook_mode.target_temperature > 0
            ):
                return cook_mode.target_temperature
        except:
            pass
        return None

    @property
    def min_temp(self) -> int:
        """Return the minimum temperature."""
        min_temp, _ = self.appliance.get_erd_value(ErdCode.OVEN_MODE_MIN_MAX_TEMP)
        return min_temp

    @property
    def max_temp(self) -> int:
        """Return the maximum temperature."""
        _, max_temp = self.appliance.get_erd_value(ErdCode.OVEN_MODE_MIN_MAX_TEMP)
        return max_temp

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None: # type: ignore
        data = {}

        cook_time_remaining = self.appliance.get_erd_value(ErdCode.ADVANTIUM_COOK_TIME_REMAINING)
        kitchen_timer = self.appliance.get_erd_value(ErdCode.ADVANTIUM_KITCHEN_TIME_REMAINING)
        data["unit_type"] = self._stringify(self.personality)
        if cook_time_remaining:
            data["cook_time_remaining"] = self._stringify(cook_time_remaining)
        if kitchen_timer:
            data["kitchen_timer"] = self._stringify(kitchen_timer)
        return data

    @property
    def _remote_config(self) -> ErdAdvantiumRemoteCookModeConfig:
        return self.appliance.get_erd_value(ErdCode.ADVANTIUM_REMOTE_COOK_MODE_CONFIG)  

    async def async_set_operation_mode(self, operation_mode: str):
        """Set the operation mode."""

        #try to get the mode/setting for the selection
        try:
            mode = AdvantiumOperationMode(operation_mode)
            setting = ADVANTIUM_OPERATION_MODE_COOK_SETTING_MAPPING[mode]
        except:
            _LOGGER.debug(f"Attempted to set mode to {operation_mode}, unknown.")
            return

        #determine the target temp for this mode
        target_temp = self._convert_target_temperature(setting.target_temperature_120v_f, setting.target_temperature_240v_f)

        #if we allow temperature to be set in this mode, and already have a temperature, use it
        if (
            setting.allow_temperature_set and 
            self.current_cook_status.cook_mode == setting.cook_mode and 
            self.target_temperature):
            target_temp = max(self.min_temp, min(self.max_temp, int(self.target_temperature)))

        #by default we will start an operation, but handle other actions too
        action = AdvantiumCookAction.START
        if mode == AdvantiumOperationMode.OFF:
            action = AdvantiumCookAction.STOP
        elif self.current_cook_setting.cook_action == AdvantiumCookAction.PAUSE:
            action = AdvantiumCookAction.RESUME
        elif self.current_cook_setting.cook_action in [AdvantiumCookAction.START, AdvantiumCookAction.RESUME]:
            action = AdvantiumCookAction.UPDATED

        #construct the new mode based on the existing mode
        new_cook_mode = ErdAdvantiumCookSetting(
            d=randrange(255),
            cook_action=action,
            cook_mode=setting.cook_mode,
            target_temperature=target_temp or 0,
            power_level=setting.target_power_level or 0,
            warm_status=setting.warm_status or AdvantiumWarmStatus.OFF,
        )
        _LOGGER.debug("New ErdAdvantiumCookSetting: %s", new_cook_mode)

        await self.appliance.async_set_erd_value(ErdCode.ADVANTIUM_COOK_SETTING, new_cook_mode)

    async def async_set_temperature(self, **kwargs):
        """Set the cook temperature"""

        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return

        #get the current mode/operation
        mode = self.current_operation_mode
        setting = self.current_operation_setting

        #if we can't figure out the mode/setting, exit
        if mode is None or setting is None:
            return 

        #if we're off or can't set temperature, just exit
        if mode == AdvantiumOperationMode.OFF or not setting.allow_temperature_set:
            return

        #should only need to update
        action = AdvantiumCookAction.UPDATED

        #construct the new mode based on the existing mode
        current_cook_mode = self.current_cook_setting
        new_cook_mode = current_cook_mode._replace(
            d = randrange(255),
            target_temperature = target_temp,
            cook_action = action,
        )

        await self.appliance.async_set_erd_value(ErdCode.ADVANTIUM_COOK_SETTING, new_cook_mode)            

    def _ensure_operation_mode(self):
        cook_status = self.current_cook_status
        cook_mode = cook_status.cook_mode  

        #if we have a current mode
        if(self._current_operation_mode is not None):
            #and the cook mode is the same as what the appliance says, we'll just leave things alone
            #and assume that things are in sync
            if ADVANTIUM_OPERATION_MODE_COOK_SETTING_MAPPING[self._current_operation_mode].cook_mode == cook_mode:
                return
            self._current_operation_mode = None
        
        #synchronize the operation mode with the device state
        if cook_mode == AdvantiumCookMode.MICROWAVE:
            #microwave matches on cook mode and power level
            if cook_status.power_level == 3:
                self._current_operation_mode = AdvantiumOperationMode.MICROWAVE_PL3
            elif cook_status.power_level == 5:
                self._current_operation_mode = AdvantiumOperationMode.MICROWAVE_PL5
            elif cook_status.power_level == 7:
                self._current_operation_mode = AdvantiumOperationMode.MICROWAVE_PL7
            else:
                self._current_operation_mode = AdvantiumOperationMode.MICROWAVE_PL10
        elif cook_mode == AdvantiumCookMode.WARM:
            for key, value in ADVANTIUM_OPERATION_MODE_COOK_SETTING_MAPPING.items():
                #warm matches on the mode, warm status, and target temp
                if (cook_mode == value.cook_mode and 
                    cook_status.warm_status == value.warm_status and 
                    cook_status.temperature == self._convert_target_temperature(
                        value.target_temperature_120v_f, value.target_temperature_240v_f)):
                    self._current_operation_mode = key
                    break

        #just pick the first match based on cook mode if we made it here
        if self._current_operation_mode is None:
            for key, value in ADVANTIUM_OPERATION_MODE_COOK_SETTING_MAPPING.items():
                if cook_mode == value.cook_mode:
                    self._current_operation_mode = key
                    break
        
        _LOGGER.debug("Operation mode is set to %s", self._current_operation_mode)
        return

    def _convert_target_temperature(self, temp_120v: Optional[int], temp_240v: Optional[int]):
        unit_type = self.personality        
        target_temp_f = temp_240v if unit_type in [ErdPersonality.PERSONALITY_240V_MONOGRAM, ErdPersonality.PERSONALITY_240V_CAFE, ErdPersonality.PERSONALITY_240V_STANDALONE_CAFE] else temp_120v
        return target_temp_f

    async def async_device_update(self, warning: bool = True) -> None:
        await super().async_device_update(warning=warning)
        self._ensure_operation_mode()        
