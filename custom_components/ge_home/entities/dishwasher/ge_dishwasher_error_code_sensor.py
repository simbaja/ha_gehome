from ..common import GeErdSensor


class GeDishwasherErrorCodeSensor(GeErdSensor):
    """Dishwasher error code, shown as the raw hex value the appliance sends.

    "0000" means no error. The SDK's ErdErrorStateConverter does not decode
    these values usefully (it keeps only the low nibble), and the upper drawer's
    error ERD (0x3208) has no converter at all, so the raw value is used instead.
    """

    @property
    def native_value(self) -> str | None:  # type: ignore
        try:
            raw = self.appliance.get_raw_erd_value(self.erd_code)
        except (KeyError, ValueError):
            return None
        return str(raw).upper() if raw is not None else None
