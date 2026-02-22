from typing import Optional

from gehomesdk import CooktopStatus

from .ge_erd_binary_sensor import GeErdBinarySensor


class GeCooktopStatusBinarySensor(GeErdBinarySensor):
    """Binary sensor that reports if any cooktop burner is active."""

    @property
    def is_on(self) -> Optional[bool]:
        """Return True when any burner that exists is reported as on."""
        try:
            status = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None

        if status is None:
            return None

        if not isinstance(status, CooktopStatus):
            return self._boolify(status)

        burners = status.burners or {}

        for burner in burners.values():
            exists = getattr(burner, "exists", False)
            is_on = self._boolify(getattr(burner, "on", None))
            if exists and is_on:
                return True

        boolify_op = getattr(status, "boolify", None)
        if callable(boolify_op):
            return boolify_op()

        return False
