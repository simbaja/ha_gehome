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
from .ucim import UcimApi
from .coffee_maker import CcmApi
from .dual_dishwasher import DualDishwasherApi
from .espresso_maker import EspressoMakerApi
from .dehumidifier import DehumidifierApi

_LOGGER = logging.getLogger(__name__)


def get_appliance_api_type(appliance_type: ErdApplianceType) -> Type:
    """Get the appropriate appliance type"""
    _LOGGER.debug(f"Found device type: {appliance_type}")
    known_types = {
        ErdApplianceType.OVEN: OvenApi,
        ErdApplianceType.COOKTOP: CooktopApi,
        ErdApplianceType.ELECTRIC_COOKTOP: CooktopApi,
        ErdApplianceType.FRIDGE: FridgeApi,
        ErdApplianceType.BEVERAGE_CENTER: FridgeApi,
        ErdApplianceType.DISH_WASHER: DishwasherApi,
        ErdApplianceType.DUAL_DISH_WASHER: DualDishwasherApi,
        ErdApplianceType.WASHER: WasherApi,
        ErdApplianceType.DRYER: DryerApi,
        ErdApplianceType.COMBINATION_WASHER_DRYER: WasherDryerApi,
        ErdApplianceType.POE_WATER_FILTER: WaterFilterApi,
        ErdApplianceType.WATER_SOFTENER: WaterSoftenerApi,
        ErdApplianceType.WATER_HEATER: WaterHeaterApi,
        ErdApplianceType.ADVANTIUM: AdvantiumApi,
        ErdApplianceType.AIR_CONDITIONER: WacApi,
        ErdApplianceType.SPLIT_AIR_CONDITIONER: SacApi,
        ErdApplianceType.PORTABLE_AIR_CONDITIONER: PacApi,
        ErdApplianceType.BUILT_IN_AIR_CONDITIONER: BiacApi,
        ErdApplianceType.HOOD: HoodApi,
        ErdApplianceType.MICROWAVE: MicrowaveApi,
        ErdApplianceType.OPAL_ICE_MAKER: OimApi,
        ErdApplianceType.UNDER_COUNTER_ICE_MAKER: UcimApi,
        ErdApplianceType.CAFE_COFFEE_MAKER: CcmApi,
        ErdApplianceType.ESPRESSO_MAKER: EspressoMakerApi,
        ErdApplianceType.DEHUMIDIFIER: DehumidifierApi
    }

    # Get the appliance type
    return known_types.get(appliance_type, ApplianceApi)
