import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType
)

from .base import ApplianceApi
from ..entities import (
    GeErdBinarySensor,
    GeErdButton
)

_LOGGER = logging.getLogger(__name__)


class EspressoMakerApi(ApplianceApi):
    """API class for Espresso Maker objects"""
    APPLIANCE_TYPE = ErdApplianceType.ESPRESSO_MAKER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        em_entities = [                   
            GeErdBinarySensor(self, ErdCode.CCM_IS_DESCALING, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdButton(self, ErdCode.CCM_CANCEL_DESCALING, entity_category=EntityCategory.CONFIG),
            GeErdButton(self, ErdCode.CCM_START_DESCALING, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.CCM_OUT_OF_WATER, device_class_override="problem", entity_category=EntityCategory.DIAGNOSTIC),
        ]

        entities = base_entities + em_entities
        return entities
