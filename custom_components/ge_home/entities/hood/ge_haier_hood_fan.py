import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)


class HaierHoodFanOptionsConverter(OptionsConverter):
    """Converter for Haier hood fan speed options."""

    # Assuming Haier hoods only support OFF / LOW / MED / HIGH
    VALID_OPTIONS = ["OFF", "LOW", "MEDIUM", "HIGH"]

    @property
    def options(self) -> List[str]:
        return self.VALID_OPTIONS

    def from_option_string(self, value: str) -> Any:
        try:
            return value.upper()
        except Exception:
            _LOGGER.warning(f"Invalid Haier hood fan option: {value}")
            return "OFF"

    def to_option_string(self, value: Any) -> Optional[str]:
        try:
            return str(value).upper()
        except Exception:
            return "OFF"


class GeHaierHoodFan(GeErdSelect):
    """Select entity for Haier hood fan speed."""

    def __init__(self, api: ApplianceApi, erd_code: str):
        super().__init__(api, erd_code, HaierHoodFanOptionsConverter())
