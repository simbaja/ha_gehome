"""Options converters for common appliance configuration ERDs.

These ERDs (sound level, end-of-cycle tone, clock format) are reported by
most Cafe/GE Profile ovens and ranges but the SDK enums do not implement
`stringify()`, so a plain GeErdSensor would render them as
"ErdSoundLevel.HIGH".  These converters give clean, writable select entities.
"""

import logging
from typing import Any, List, Optional

from gehomesdk import ErdClockFormat, ErdEndTone, ErdSoundLevel

from .options_converter import OptionsConverter

_LOGGER = logging.getLogger(__name__)


class _EnumOptionsConverter(OptionsConverter):
    """Generic name<->title-case converter for simple SDK enums."""

    _enum: Any = None
    _excluded: tuple = ()
    _fallback: Any = None

    @property
    def options(self) -> List[str]:
        return [self._to_str(i) for i in self._enum if i not in self._excluded]

    def from_option_string(self, value: str) -> Any:
        try:
            return self._enum[value.upper().replace(" ", "_")]
        except KeyError:
            _LOGGER.warning(
                "Could not map '%s' to %s, falling back to %s",
                value,
                self._enum.__name__,
                self._fallback,
            )
            return self._fallback

    def to_option_string(self, value: Any) -> Optional[str]:
        if value is None or value in self._excluded:
            return None
        try:
            return self._to_str(value)
        except Exception:  # noqa: BLE001 - defensive, never break the entity
            return None

    @staticmethod
    def _to_str(value: Any) -> str:
        return value.name.replace("_", " ").title()


class SoundLevelOptionsConverter(_EnumOptionsConverter):
    """0x000A - SOUND_LEVEL: Off / Low / Standard / High."""

    _enum = ErdSoundLevel
    _fallback = ErdSoundLevel.STANDARD


class EndToneOptionsConverter(_EnumOptionsConverter):
    """0x5001 - END_TONE: Beep / Repeated Beep."""

    _enum = ErdEndTone
    _excluded = (ErdEndTone.NA,)
    _fallback = ErdEndTone.BEEP


class ClockFormatOptionsConverter(_EnumOptionsConverter):
    """0x0006 - CLOCK_FORMAT: Twelve Hour / Twenty Four Hour / No Display."""

    _enum = ErdClockFormat
    _fallback = ErdClockFormat.TWELVE_HOUR
