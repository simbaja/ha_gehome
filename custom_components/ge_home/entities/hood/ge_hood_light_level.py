from typing import Optional
from gehomesdk import ErdCodeType
from ...devices import ApplianceApi
from ..common import GeErdSelect
from .ge_hood_light_options import detect_hood_light_level

class GeHoodLightLevelSelect(GeErdSelect):
    def __init__(
            self,
            api: ApplianceApi,
            erd_code: ErdCodeType,
            control_erd_code: Optional[ErdCodeType] = None,
            enabled_default: bool = True
        ):
        self._availability, converter = detect_hood_light_level(api)
        self._attr_entity_registry_enabled_default = enabled_default
        super().__init__(api, erd_code, converter, control_erd_code=control_erd_code)
