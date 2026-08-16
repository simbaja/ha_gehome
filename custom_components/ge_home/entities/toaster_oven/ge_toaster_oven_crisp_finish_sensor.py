"""GE Home toaster oven crisp finish sensor."""

from propcache.api import cached_property

from homeassistant.const import EntityCategory
from gehomesdk import ErdCode, ErdToasterOvenCookMode, ToasterOvenCookSetting

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdBinarySensor


class GeToasterOvenCrispFinishSensor(GeErdBinarySensor):
    """Sensor describing whether Crisp Finish is selected."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            ErdCode.TOASTER_OVEN_COOK_SETTING,
            "toaster_oven_crisp_finish",
            "mdi:fan",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.entity_identifier}_toaster_oven_crisp_finish"

    @cached_property
    def name(self) -> str | None:
        return f"{self.entity_identifier} Toaster Oven Crisp Finish"

    @property
    def is_on(self) -> bool | None:  # type: ignore
        try:
            setting = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if not isinstance(setting, ToasterOvenCookSetting):
            return None
        return setting.cook_mode == ErdToasterOvenCookMode.CRISP_FINISH
