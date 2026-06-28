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
            is_zero(self.serial_number) and
            self.serial_number.isprintable()):
            return self.serial_number
        if self.serial_number and not self.serial_number.isprintable():
            _LOGGER.warning(
                "Serial number for %s contains non-printable characters "
                "(possible certificate data on ERD 0x0002); falling back to MAC address.",
                self.mac_addr,
            )
        return self.mac_addr

    @cached_property
    def brand_id(self) -> ErdBrand:
        """Resolve the appliance brand, inferring from the model number when
        the BRAND ERD is absent or unknown."""
        b: ErdBrand | None = self.try_get_erd_value(ErdCode.BRAND)

        if b in (None, ErdBrand.UNKNOWN, ErdBrand.NOT_DEFINED):
            inferred = self._infer_brand_from_model(self.model_number)
            b = inferred or ErdBrand.GE

        return b

    @cached_property
    def brand(self) -> str:
        return ERD_BRAND_NAME_MAP.get(self.brand_id, 'GE')

    @property
    def is_fisher_paykel(self) -> bool:
        """Whether this appliance is Fisher & Paykel branded.

        F&P appliances differ from GE here: metric-market F&P models report
        their raw ERD temperatures in Celsius, whereas GE appliances always
        report Fahrenheit (and may report a METRIC unit while still sending
        Fahrenheit).  Used to decide whether the device's TEMPERATURE_UNIT can
        be trusted for temperature reporting."""
        return self.brand_id in (ErdBrand.FISHER_PAYKEL, ErdBrand.HEIER_FPA)
    
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
        from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
        from ..entities import GeErdSensor, GeErdSwitch, GeErdPropertySensor
        entities = [
            GeErdSensor(self, ErdCode.CLOCK_TIME, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSwitch(self, ErdCode.SABBATH_MODE),
        ]

        # Resource monitoring sensors - available on supported appliances
        # build_entities_list filters these against known_properties automatically
        entities += [
            GeErdSensor(self, ErdCode.RESOURCE_DEMAND_RESPONSE_STATE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.RESOURCE_CUMULATIVE_ENERGY,
                uom_override="Wh",
                device_class_override=SensorDeviceClass.ENERGY,
                state_class_override=SensorStateClass.TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.RESOURCE_CUMULATIVE_COLD_WATER_LITERS,
                uom_override="L",
                device_class_override=SensorDeviceClass.WATER,
                state_class_override=SensorStateClass.TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.RESOURCE_CUMULATIVE_HOT_WATER_LITERS,
                uom_override="L",
                device_class_override=SensorDeviceClass.WATER,
                state_class_override=SensorStateClass.TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.RESOURCE_CUMULATIVE_GAS_CUBIC_FEET,
                uom_override="ft³",
                device_class_override=SensorDeviceClass.GAS,
                state_class_override=SensorStateClass.TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC),
        ]

        entities.append(
            GeErdPropertySensor(
                self,
                ErdCode.RESOURCE_DSM_POWER_USAGE,
                "instantaneous_power_w",
                uom_override="W",
                device_class_override=SensorDeviceClass.POWER,
                state_class_override=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
            )
        )

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
        for prefix, brand_or_idx in BRAND_SPECIAL_PREFIXES.items():
            if m.startswith(prefix):
                if isinstance(brand_or_idx, ErdBrand):
                    _LOGGER.debug(f"Model '{m}': inferred brand '{brand_or_idx.name}' from prefix '{prefix}'")
                    return brand_or_idx

                idx = brand_or_idx
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
