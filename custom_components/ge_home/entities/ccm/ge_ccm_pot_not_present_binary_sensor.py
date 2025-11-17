from propcache.api import cached_property

from ..common import GeErdBinarySensor

class GeCcmPotNotPresentBinarySensor(GeErdBinarySensor):
    @cached_property
    def is_on(self) -> bool:
        """Return True if entity is not pot present."""
        return not self._boolify(self.appliance.get_erd_value(self.erd_code))
    
