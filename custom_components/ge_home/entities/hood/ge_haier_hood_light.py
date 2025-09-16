import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)


class HaierHoodLightOptionsConverter(OptionsConverter):
    """Converter for Haier hood light level options."""

    # Assuming Haier hoods support OFF / DIM / HIGH
    VALID_OPTIONS = ["OFF", "DIM", "HIGH"]

    @property
    def options(self) -> List[str]:
        return self.VALID_OPTIONS

    def from_option_string(self, value: str) -> Any:
        try:
            return value.upper()
        except Exception:
            _LOGGER.warning(f"Invalid Haier hood light option: {value}")
            return "OFF"

    def to_option_string(self, value: Any) -> Optional[str]:
        try:
            return str(value).upper()
        except Exception:
            return "OFF"


class GeHaierHoodLight(GeErdSelect):
    """Select entity for Haier hood light level."""

    def __init__(self, api: ApplianceApi, erd_code: str):
        super().__init__(api, erd_code, HaierHoodLightOptionsConverter())
