import logging
from typing import Type

from gehomesdk.erd import ErdApplianceType

from .base import ApplianceApi
from .oven import OvenApi
from .cooktop import CooktopApi
from .fridge import FridgeApi
from .dishwasher import DishwasherApi
from .washer import WasherApi
from .dryer import DryerApi
from .washer_dryer import WasherDryerApi
from .water_filter import WaterFilterApi
from .advantium import AdvantiumApi
from .wac import WacApi
from .sac import SacApi
from .pac import PacApi
from .biac import BiacApi
from .hood import HoodApi
from .microwave import MicrowaveApi
from .water_softener import WaterSoftenerApi
from .water_heater import WaterHeaterApi
from .oim import OimApi
from .coffee_maker import CcmApi
from .dual_dishwasher import DualDishwasherApi
from .espresso_maker import EspressoMakerApi
from .dehumidifier import DehumidifierApi

_LOGGER = logging.getLogger(__name__)


def get_appliance_api_type(appliance_type: ErdApplianceType) -> Type:
    """Get the appropriate appliance type"""
    _LOGGER.debug(f"Found device type: {appliance_type}")
    if appliance_type == ErdApplianceType.OVEN:
        return OvenApi
    if appliance_type == ErdApplianceType.COOKTOP:
        return CooktopApi
    if appliance_type == ErdApplianceType.ELECTRIC_COOKTOP:
        return CooktopApi
    if appliance_type == ErdApplianceType.FRIDGE:
        return FridgeApi
    if appliance_type == ErdApplianceType.BEVERAGE_CENTER:
        return FridgeApi
    if appliance_type == ErdApplianceType.DISH_WASHER:
        return DishwasherApi
    if appliance_type == ErdApplianceType.DUAL_DISH_WASHER:
        return DualDishwasherApi
    if appliance_type == ErdApplianceType.WASHER:
        return WasherApi
    if appliance_type == ErdApplianceType.DRYER:
        return DryerApi
    if appliance_type == ErdApplianceType.COMBINATION_WASHER_DRYER:
        return WasherDryerApi
    if appliance_type == ErdApplianceType.POE_WATER_FILTER:
        return WaterFilterApi
    if appliance_type == ErdApplianceType.WATER_SOFTENER:
        return WaterSoftenerApi
    if appliance_type == ErdApplianceType.WATER_HEATER:
        return WaterHeaterApi
    if appliance_type == ErdApplianceType.ADVANTIUM:
        return AdvantiumApi
    if appliance_type == ErdApplianceType.AIR_CONDITIONER:
        return WacApi
    if appliance_type == ErdApplianceType.SPLIT_AIR_CONDITIONER:
        return SacApi
    if appliance_type == ErdApplianceType.PORTABLE_AIR_CONDITIONER:
        return PacApi
    if appliance_type == ErdApplianceType.BUILT_IN_AIR_CONDITIONER:
        return BiacApi
    if appliance_type == ErdApplianceType.HOOD:
        return HoodApi
    if appliance_type == ErdApplianceType.MICROWAVE:
        return MicrowaveApi        
    if appliance_type == ErdApplianceType.OPAL_ICE_MAKER:
        return OimApi
    if appliance_type == ErdApplianceType.CAFE_COFFEE_MAKER:
        return CcmApi
    if appliance_type == ErdApplianceType.ESPRESSO_MAKER:
        return EspressoMakerApi
    if appliance_type == ErdApplianceType.DEHUMIDIFIER:
        return DehumidifierApi

    # Fallback
    return ApplianceApi
