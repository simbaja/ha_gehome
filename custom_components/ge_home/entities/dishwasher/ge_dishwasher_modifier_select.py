import logging
from typing import Any, List, Optional

from gehomesdk import ErdCodeType
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

# The F&P wash modifier lives in a standalone 1-byte register (lower 0x3086 / upper 0x3222) that the
# SDK reports as an "unknown" ERD (raw bytes).  Encoding confirmed by labeled live capture 2026-07-23,
# and cloud writes were verified to both hold AND light up the physical panel (real selection).
# The three modifier bits are mutually exclusive on the panel; MASK covers all of them so a write
# replaces the current modifier and any co-located bits outside the mask survive.
MODIFIER_MASK = 0x46
MODIFIER_TO_VALUE = {
    "None": 0x00,
    "Extra Dry": 0x40,
    "Quick": 0x02,
    "Sanitize": 0x04,
}
VALUE_TO_MODIFIER = {v: k for k, v in MODIFIER_TO_VALUE.items()}


class DishwasherModifierOptionsConverter(OptionsConverter):
    """Maps between the masked modifier value (int) and its F&P panel label."""

    @property
    def options(self) -> List[str]:
        return list(MODIFIER_TO_VALUE.keys())

    def from_option_string(self, value: str) -> Any:
        return MODIFIER_TO_VALUE.get(value)

    def to_option_string(self, value: Any) -> Optional[str]:
        # `value` is the already-masked modifier byte (an int).
        return VALUE_TO_MODIFIER.get(value)


class GeDishwasherModifierSelect(GeErdSelect):
    """Selects the F&P wash modifier (None / Extra Dry / Quick / Sanitize).

    Reads and writes the modifier register directly.  Because it's an "unknown" ERD the SDK can't
    encode, we read the raw byte, set the modifier bits (read-modify-write with MODIFIER_MASK so
    unobserved co-located bits survive), and push the raw hex down the client — the same raw path the
    program select uses.  NOTE: selecting a program on the panel clears the modifier (observed), so the
    current option can change out from under a set without a write here — that's normal appliance
    behavior, reflected on the next state push.
    """

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, erd_override: Optional[str] = None,
                 icon_override: Optional[str] = None):
        super().__init__(api, erd_code, DishwasherModifierOptionsConverter(),
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
        # None (unknown) for an unrecognized combination rather than guessing a wrong label.
        return self._converter.to_option_string(n & MODIFIER_MASK)

    async def async_select_option(self, option: str) -> None:
        target = self._converter.from_option_string(option)
        if target is None:
            _LOGGER.warning(f"Unknown dishwasher modifier {option!r}; ignoring")
            return

        raw = self.appliance.get_raw_erd_value(self.erd_code)
        try:
            cur = int(raw, 16)
        except (TypeError, ValueError):
            _LOGGER.warning(f"Cannot set modifier: current {self.erd_code} value {raw!r} is not readable")
            return

        new = (cur & ~MODIFIER_MASK) | (target & MODIFIER_MASK)
        if new == cur:
            return

        # Preserve the exact hex width (and case) the appliance uses.
        new_hex = format(new, f"0{len(raw)}x")
        if raw != raw.lower():
            new_hex = new_hex.upper()

        _LOGGER.debug(f"Setting {self.erd_code} modifier {self.current_option!r} -> {option!r} "
                      f"(raw {raw} -> {new_hex}, mask 0x{MODIFIER_MASK:02X})")
        # Raw write — deliberately bypasses appliance.async_set_erd_value / the typed encoder.
        await self.appliance.client.async_set_erd_value(self.appliance, self.erd_code, new_hex)
