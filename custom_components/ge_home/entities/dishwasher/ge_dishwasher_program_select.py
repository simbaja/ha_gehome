import logging
from typing import Any, List, Optional

from gehomesdk import ErdCodeType
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

# Fisher & Paykel wash programs are identified by the LOW BYTE (bits 1-4, mask 0x1E) of the
# user-setting word (0x3007 lower / 0x3207 upper).  Confirmed at the physical panel 2026-07-23.
# The GE `cycle_mode` slice (bits 1-3) is too narrow to distinguish them — e.g. Fast (0x12) and
# Heavy (0x02) both decode to GE cycle_mode 1 — so we key on the whole low nibble+bit4 instead.
PROGRAM_MASK = 0x1E
PROGRAM_TO_VALUE = {
    "Heavy": 0x02,
    "Medium": 0x04,
    "Eco": 0x0C,
    "Rinse": 0x0E,
    "Delicate": 0x10,
    "Fast": 0x12,
}
VALUE_TO_PROGRAM = {v: k for k, v in PROGRAM_TO_VALUE.items()}


class DishwasherProgramOptionsConverter(OptionsConverter):
    """Maps between the masked program value (int) and its F&P panel label."""

    @property
    def options(self) -> List[str]:
        return list(PROGRAM_TO_VALUE.keys())

    def from_option_string(self, value: str) -> Any:
        return PROGRAM_TO_VALUE.get(value)

    def to_option_string(self, value: Any) -> Optional[str]:
        # `value` is the already-masked program value (an int).
        return VALUE_TO_PROGRAM.get(value)


class GeDishwasherProgramSelect(GeErdSelect):
    """Selects the F&P wash program by read-modify-writing the user-setting low byte.

    Why this overrides the base read/write path:
      * READ — the base reads GE's decoded `cycle_mode`, which mislabels F&P programs.  We read the
        RAW word and key on the low byte instead.
      * WRITE — the base writes via `appliance.async_set_erd_value`, which routes through the SDK's
        `ErdUserSettingConverter.erd_encode`.  That encoder rebuilds the word from only the GE-known
        fields (dropping the F&P program bits beyond bit 3, wash_zone, etc.) and encodes it at the
        default 2-byte length, overflowing once delay/zone bits are set.  It would corrupt the word.
        Instead we read the raw hex, flip only bits 1-4, and push the raw string down the client,
        preserving every co-located bit.  Raw-write control was verified on the appliance 2026-07-23.
    """

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, erd_override: Optional[str] = None,
                 icon_override: Optional[str] = None):
        super().__init__(api, erd_code, DishwasherProgramOptionsConverter(),
                         erd_override=erd_override, icon_override=icon_override)

    def _current_int(self) -> Optional[int]:
        raw = self.appliance.get_raw_erd_value(self.erd_code)
        try:
            return int(raw, 16)
        except (TypeError, ValueError):
            return None

    @property
    def current_option(self) -> Optional[str]:  # type: ignore
        n = self._current_int()
        if n is None:
            return None
        # Returns None for an unrecognized program value rather than guessing a wrong label.
        return self._converter.to_option_string(n & PROGRAM_MASK)

    async def async_select_option(self, option: str) -> None:
        target = self._converter.from_option_string(option)
        if target is None:
            _LOGGER.warning(f"Unknown dishwasher program {option!r}; ignoring")
            return

        raw = self.appliance.get_raw_erd_value(self.erd_code)
        try:
            cur = int(raw, 16)
        except (TypeError, ValueError):
            _LOGGER.warning(f"Cannot set program: current {self.erd_code} value {raw!r} is not readable")
            return

        new = (cur & ~PROGRAM_MASK) | (target & PROGRAM_MASK)
        if new == cur:
            return

        # Preserve the exact hex width (and case) the appliance uses.
        new_hex = format(new, f"0{len(raw)}x")
        if raw != raw.lower():
            new_hex = new_hex.upper()

        _LOGGER.debug(f"Setting {self.erd_code} program {self.current_option!r} -> {option!r} "
                      f"(raw {raw} -> {new_hex}, mask 0x{PROGRAM_MASK:02X})")
        # Raw write — deliberately bypasses appliance.async_set_erd_value / the typed encoder.
        await self.appliance.client.async_set_erd_value(self.appliance, self.erd_code, new_hex)
