import logging
from typing import List, Any, Optional

from gehomesdk import ErdAcFanSetting
from ..common import OptionsConverter
from .const import SMART_DRY

_LOGGER = logging.getLogger(__name__)

class DehumidifierFanSettingOptionsConverter(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [SMART_DRY] + [i.stringify() for i in [ErdAcFanSetting.LOW, ErdAcFanSetting.MED, ErdAcFanSetting.HIGH]]
 
    def from_option_string(self, value: str) -> Any:
        try:
            if value == SMART_DRY:
                return ErdAcFanSetting.DEFAULT
            return ErdAcFanSetting[value.upper()]
        except:
            _LOGGER.warning(f"Could not set fan setting to {value.upper()}")
            return ErdAcFanSetting.DEFAULT
    def to_option_string(self, value: ErdAcFanSetting) -> Optional[str]:
        try:
            if value is not None:
                return SMART_DRY if value == ErdAcFanSetting.DEFAULT else value.stringify()
        except:
            pass
        return SMART_DRY
