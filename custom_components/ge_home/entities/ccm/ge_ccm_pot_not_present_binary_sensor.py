from ..common import GeErdBinarySensor

class GeCcmPotNotPresentBinarySensor(GeErdBinarySensor):
    @property
    def is_on(self) -> bool: # type: ignore
        """Return True if entity is not pot present."""
        return not self._boolify(self.appliance.get_erd_value(self.erd_code))
    
