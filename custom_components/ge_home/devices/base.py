import asyncio
import logging
from propcache.api import cached_property
from typing import Dict, List, Optional

from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from gehomesdk import (
    GeAppliance,
    ErdCode, 
    ErdCodeType, 
    ErdApplianceType,
    ERD_BRAND_NAME_MAP,
    ErdBrand
)

from .const import BRAND_FIRST_LETTER_MAP, BRAND_SPECIAL_PREFIXES
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ApplianceApi:
    """
    API class to represent a single physical device.

    Since a physical device can have many entities, we"ll pool common elements here
    """
    APPLIANCE_TYPE = None  # type: Optional[ErdApplianceType]

    def __init__(self, coordinator: DataUpdateCoordinator, appliance: GeAppliance):
        if not appliance.initialized:
            raise RuntimeError("Appliance not ready")
        self._appliance = appliance
        self._loop = appliance.client.loop
        self._hass = coordinator.hass
        self.coordinator = coordinator
        self.initial_update = False
        self._entities: Dict[str, Entity] = {}

    @property
    def hass(self) -> HomeAssistant:
        return self._hass

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        if self._loop is None:
            self._loop = self._appliance.client.loop
        return self._loop

    @property
    def appliance(self) -> GeAppliance:
        return self._appliance

    @appliance.setter
    def appliance(self, value: GeAppliance):
        self._appliance = value

    @property
    def available(self) -> bool:
        #Note - online will be there since we're using the GE coordinator
        #Didn't want to deal with the circular references to get the type hints
        #working.
        return self.appliance.available and self.coordinator.online # type: ignore

    @cached_property
    def serial_number(self) -> str:
        return self.appliance.get_erd_value(ErdCode.SERIAL_NUMBER)

    @cached_property
    def mac_addr(self) -> str:
        return self.appliance.mac_addr

    @cached_property
    def serial_or_mac(self) -> str:
        def is_zero(val: str) -> bool:
            try:
                intVal = int(val)
                return intVal == 0
            except:
                return False
    
        if (self.serial_number and not 
            self.serial_number.isspace() and not 
            is_zero(self.serial_number)):
            return self.serial_number
        return self.mac_addr

    @cached_property
    def brand(self) -> str:
        b: ErdBrand | None = self.try_get_erd_value(ErdCode.BRAND)

        if b in (None, ErdBrand.UNKNOWN, ErdBrand.NOT_DEFINED):
            inferred = self._infer_brand_from_model(self.model_number)
            b = inferred or ErdBrand.GE

        return ERD_BRAND_NAME_MAP.get(b, 'GE')
    
    @cached_property
    def model_number(self) -> str:
        return self.appliance.get_erd_value(ErdCode.MODEL_NUMBER)

    @property
    def sw_version(self) -> str:
        appVer = self.try_get_erd_value(ErdCode.APPLIANCE_SW_VERSION)
        wifiVer = self.try_get_erd_value(ErdCode.WIFI_MODULE_SW_VERSION)

        return 'Appliance=' + str(appVer or 'Unknown') + '/Wifi=' + str(wifiVer or 'Unknown')

    @cached_property
    def name(self) -> str:
        appliance_type = self.appliance.appliance_type
        if appliance_type is None or appliance_type == ErdApplianceType.UNKNOWN:
            appliance_type = "Appliance"
        else:
            appliance_type = appliance_type.name.replace("_", " ").title()
        return f"{self.brand} {appliance_type} {self.serial_or_mac}"

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""

        return {
            "identifiers": {(DOMAIN, self.mac_addr)},
            "serial_number": self.serial_number,
            "name": self.name,
            "manufacturer": self.brand,
            "model": self.model_number,
            "sw_version": self.sw_version
        }

    @property
    def entities(self) -> List[Entity]:       
        return list(self._entities.values())

    def get_all_entities(self) -> List[Entity]:
        """Create Entities for this device."""
        return self.get_base_entities()

    def get_base_entities(self) -> List[Entity]:
        """Create base entities (i.e. common between all appliances)."""
        from ..entities import GeErdSensor, GeErdSwitch
        entities = [
            GeErdSensor(self, ErdCode.CLOCK_TIME, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSwitch(self, ErdCode.SABBATH_MODE),
        ]
        return entities        

    def build_entities_list(self) -> None:
        """Build the entities list, adding anything new."""
        from ..entities import GeErdEntity, GeErdButton
        entities = [
            e for e in self.get_all_entities()
            if not isinstance(e, GeErdEntity) or isinstance(e, GeErdButton) or e.erd_code in self.appliance.known_properties
        ]

        for entity in entities:
            if entity.unique_id is not None and entity.unique_id not in self._entities:
                self._entities[entity.unique_id] = entity

    def try_get_erd_value(self, code: ErdCodeType):
        try:
            return self.appliance.get_erd_value(code)
        except:
            return None
    
    def has_erd_code(self, code: ErdCodeType):
        try:
            self.appliance.get_erd_value(code)
            return True
        except:
            return False

    def _infer_brand_from_model(self, model: str) -> Optional[ErdBrand]:
        """
        Infer the appliance brand from model number using first-letter mapping
        and special prefix handling.
        """
        if not model:
            _LOGGER.debug("Model number is empty, cannot infer brand.")
            return None

        m = model.strip().upper()

        # Try special prefixes
        for prefix, idx in BRAND_SPECIAL_PREFIXES.items():
            if m.startswith(prefix):
                if len(m) > idx:
                    brand_letter = m[idx]
                    brand = BRAND_FIRST_LETTER_MAP.get(brand_letter)
                    if brand:
                        _LOGGER.debug(f"Model '{m}': inferred brand '{brand.name}' from prefix '{prefix}' at position {idx + 1}")
                        return brand
                _LOGGER.debug(f"Model '{m}': prefix '{prefix}' found but brand letter at position {idx + 1} not recognized")
                return None

        # Try general
        first_letter = m[0]
        brand = BRAND_FIRST_LETTER_MAP.get(first_letter)
        if brand:
            _LOGGER.debug(f"Model '{m}': inferred brand '{brand.name}' from first letter '{first_letter}'")
            return brand

        # Log and return
        _LOGGER.debug(f"Model '{m}': could not infer brand (first letter '{first_letter}' not in mapping)")
        return None