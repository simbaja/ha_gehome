""" Home Assistant derived exceptions"""

from homeassistant import exceptions as ha_exc

class HaCannotConnect(ha_exc.HomeAssistantError):
    """Error to indicate we cannot connect."""
class HaAuthError(ha_exc.HomeAssistantError):
    """Error to indicate authentication failure."""
class HaMfaRequired(ha_exc.HomeAssistantError):
    """Error to indicate MFA is required to complete login."""
class HaTermsRequired(ha_exc.HomeAssistantError):
    """Error to indicate terms of service acceptance is required."""
class HaAlreadyConfigured(ha_exc.HomeAssistantError):
    """Error to indicate that the account is already configured"""
class HaInvalidOperation(ha_exc.HomeAssistantError):
    """Error to indcate that an invalid operation was attempted"""