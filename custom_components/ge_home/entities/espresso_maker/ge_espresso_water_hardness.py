import logging
from typing import List, Any, Optional

from homeassistant.const import EntityCategory
from gehomesdk import ErdCode, ErdEspressoWaterHardness
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class GeEspressoWaterHardnessOptionsConverter(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in ErdEspressoWaterHardness if i != ErdEspressoWaterHardness.UNKNOWN]

    def from_option_string(self, value: str) -> Any:
        return ErdEspressoWaterHardness[value.upper().replace(" ", "_")]

    def to_option_string(self, value: ErdEspressoWaterHardness) -> Optional[str]:
        if value == ErdEspressoWaterHardness.UNKNOWN:
            return None
        return value.stringify()

class GeEspressoWaterHardnessSelect(GeErdSelect):
    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            ErdCode.ESPRESSO_WATER_HARDNESS,
            GeEspressoWaterHardnessOptionsConverter(),
            icon_override="mdi:water-opacity",
            control_erd_code=ErdCode.ESPRESSO_REQUESTED_WATER_HARDNESS,
            entity_category=EntityCategory.CONFIG
        )
