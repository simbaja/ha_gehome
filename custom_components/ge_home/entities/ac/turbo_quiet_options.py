from typing import Any, List, Optional

from gehomesdk import ErdAcTurboQuietMode

from ..common import OptionsConverter

TURBO_QUIET_MODE_NORMAL = "Normal"
TURBO_QUIET_MODE_TURBO = "Turbo"
TURBO_QUIET_MODE_QUIET = "Quiet"


class TurboQuietModeOptionsConverter(OptionsConverter):
    def __init__(self, has_turbo: bool = True, has_quiet: bool = True):
        self._has_turbo = has_turbo
        self._has_quiet = has_quiet

    @property
    def options(self) -> List[str]:
        opts = [TURBO_QUIET_MODE_NORMAL]
        if self._has_turbo:
            opts.append(TURBO_QUIET_MODE_TURBO)
        if self._has_quiet:
            opts.append(TURBO_QUIET_MODE_QUIET)
        return opts

    def from_option_string(self, value: str) -> Any:
        return {
            TURBO_QUIET_MODE_NORMAL: ErdAcTurboQuietMode.NORMAL,
            TURBO_QUIET_MODE_TURBO: ErdAcTurboQuietMode.TURBO,
            TURBO_QUIET_MODE_QUIET: ErdAcTurboQuietMode.QUIET,
        }.get(value, ErdAcTurboQuietMode.NORMAL)

    def to_option_string(self, value: Any) -> Optional[str]:
        return {
            ErdAcTurboQuietMode.NORMAL: TURBO_QUIET_MODE_NORMAL,
            ErdAcTurboQuietMode.TURBO: TURBO_QUIET_MODE_TURBO,
            ErdAcTurboQuietMode.QUIET: TURBO_QUIET_MODE_QUIET,
        }.get(value)
