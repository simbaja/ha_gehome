"""Data update coordinator for GE Home Appliances"""

import asyncio
import async_timeout
import logging
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_REGION
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.ssl import get_default_context 

from gehomesdk import (
    EVENT_APPLIANCE_INITIAL_UPDATE,
    EVENT_APPLIANCE_UPDATE_RECEIVED,
    EVENT_CONNECTED,
    EVENT_DISCONNECTED,
    EVENT_GOT_APPLIANCE_LIST,
    ErdCodeType,
    GeAppliance,
    GeWebsocketClient,
    ErdApplianceType
)
from gehomesdk import GeAuthFailedError, GeGeneralServerError, GeNotAuthenticatedError

from .const import (
    DOMAIN,
    EVENT_ALL_APPLIANCES_READY,
    UPDATE_INTERVAL,
    MIN_RETRY_DELAY,
    MAX_RETRY_DELAY,
    RETRY_OFFLINE_COUNT,
    CLIENT_START_ASYNC_TIMEOUT,
    ROSTER_ASYNC_WAIT
)
from .devices import ApplianceApi, get_appliance_api_type
from .exceptions import HaAuthError, HaCannotConnect, HaInvalidOperation

PLATFORMS = [
    "binary_sensor", 
    "sensor", 
    "switch", 
    "water_heater", 
    "select", 
    "climate", 
    "light", 
    "button", 
    "number",
    "humidifier"
]
_LOGGER = logging.getLogger(__name__)


class GeHomeUpdateCoordinator(DataUpdateCoordinator):
    """Define a wrapper class to update GE Home data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Set up the GeHomeUpdateCoordinator class."""
        super().__init__(hass, _LOGGER, name=DOMAIN)

        self._config_entry = config_entry
        self._username = config_entry.data[CONF_USERNAME]
        self._password = config_entry.data[CONF_PASSWORD]
        self._region = config_entry.data[CONF_REGION]
        self._appliance_apis: Dict[str, ApplianceApi] = {}
        self._signal_remove_callbacks: List[Callable] = []
        self._updater_task: asyncio.Task | None = None

        self._reset_initialization()

    #region Public Properties

    @property
    def appliances(self) -> Iterable[GeAppliance]:
        if self.client is None:
            return []

        return self.client.appliances.values()

    @property
    def appliance_apis(self) -> Dict[str, ApplianceApi]:
        return self._appliance_apis
    
    @property
    def all_appliances_updated(self) -> bool:
        """True if all appliances have had an initial update."""
        return all([a.initialized for a in self.appliances])

    @property
    def signal_ready(self) -> str:
        """Event specific per entry to signal readiness"""
        return f"{DOMAIN}-ready-{self._config_entry.entry_id}"

    @property
    def initialized(self) -> bool:
        return self._init_done 

    @property
    def online(self) -> bool:
        """
        Indicates whether the services is online. If it's retried several times, it's assumed
        that it's offline for some reason
        """
        return self.connected or self._retry_count <= RETRY_OFFLINE_COUNT

    @property
    def connected(self) -> bool:
        """
        Indicates whether the coordinator is connected
        """
        return self.client is not None and self.client.connected
    
    @property
    def available(self) -> bool:
        """
        Indicates whether the coordinator is available
        """
        return self.client is not None and self.client.available
    
    #endregion

    #region Public Methods

    def add_signal_remove_callback(self, cb: Callable):
        self._signal_remove_callbacks.append(cb)

    async def async_setup(self):
        """Setup a new coordinator"""
        _LOGGER.debug("Setting up coordinator")

        await self.hass.config_entries.async_forward_entry_setups(
            self._config_entry, PLATFORMS
        )

        try:
            await self._async_start_client()
        except (GeNotAuthenticatedError, GeAuthFailedError):
            raise HaAuthError("Authentication failure")
        except GeGeneralServerError:
            raise HaCannotConnect("Cannot connect (server error)")
        except Exception as exc:
            raise HaCannotConnect("Unknown connection failure") from exc

        return True

    async def async_reset(self):
        """Resets the coordinator."""
        _LOGGER.debug("resetting the coordinator")
        entry = self._config_entry
        
        # remove all the callbacks for this coordinator
        for c in self._signal_remove_callbacks:
            c()
        self._signal_remove_callbacks.clear()

        unload_ok = await self.hass.config_entries.async_unload_platforms(
            self._config_entry, PLATFORMS
        )
        return unload_ok

    #endregion    

    #region Client Event Handlers

    async def on_device_update(self, data: Tuple[GeAppliance, Dict[ErdCodeType, Any]]):
        """Let HA know there's new state."""
        self.last_update_success = True
        appliance, update_data = data

        self._dump_appliance(appliance, update_data)
        
        if not self._is_appliance_valid(appliance):
            _LOGGER.debug(f"on_device_update: skipping invalid appliance {appliance.mac_addr}")
            return

        try:
            api = self.appliance_apis[appliance.mac_addr]
        except KeyError:
            _LOGGER.info(f"Could not find appliance {appliance.mac_addr} in known device list.")
            return
        
        self._update_entity_state(api.entities)

    async def on_appliance_list(self, _):
        """When we get an appliance list, mark it and maybe trigger all ready."""

        _LOGGER.debug("Got roster update")
        self.last_update_success = True
        if not self._got_roster:
            self._got_roster = True
            # TODO: Probably should have a better way of confirming we're good to go...
            await asyncio.sleep(ROSTER_ASYNC_WAIT)
            # After the initial roster update, wait a bit and hit go
            await self._async_maybe_trigger_all_ready()

    async def on_device_initial_update(self, appliance: GeAppliance):
        """When an appliance first becomes ready, let the system know and schedule periodic updates."""

        self._dump_appliance(appliance)

        if not self._is_appliance_valid(appliance):
            _LOGGER.debug(f"on_device_initial_update: skipping invalid appliance {appliance.mac_addr}")
            return

        _LOGGER.debug(f"Got initial update for {appliance.mac_addr}")

        self.last_update_success = True
        self._maybe_add_appliance_api(appliance)
        await self._async_maybe_trigger_all_ready()
        await self._start_periodic_updates()   

    async def on_disconnect(self, _):
        """Handle disconnection."""
        _LOGGER.debug(f"Disconnected. Attempting to reconnect in {MIN_RETRY_DELAY} seconds")
        self.last_update_success = False
        self.hass.loop.call_later(MIN_RETRY_DELAY, self._reconnect, True)

    async def on_connect(self, _):
        """Set state upon connection."""
        self.last_update_success = True
        self._retry_count = 0

    #endregion        
            
    #region Internal Methods

    #region Initialization/Reset

    def _create_ge_client(
        self, event_loop: Optional[asyncio.AbstractEventLoop]
    ) -> GeWebsocketClient:
        """
        Create a new GeClient object with some helpful callbacks.

        :param event_loop: Event loop
        :return: GeWebsocketClient
        """
        client = GeWebsocketClient(
            self._username,
            self._password,
            self._region,
            event_loop=event_loop,
            ssl_context=get_default_context()
        )
        client.add_event_handler(EVENT_APPLIANCE_INITIAL_UPDATE, self.on_device_initial_update)
        client.add_event_handler(EVENT_APPLIANCE_UPDATE_RECEIVED, self.on_device_update)
        client.add_event_handler(EVENT_GOT_APPLIANCE_LIST, self.on_appliance_list)
        client.add_event_handler(EVENT_DISCONNECTED, self.on_disconnect)
        client.add_event_handler(EVENT_CONNECTED, self.on_connect)
        return client  

    async def _get_client(self) -> GeWebsocketClient:
        """Get a new GE Websocket client."""
        if self.client:
            try:
                self.client.clear_event_handlers()
                await self.client.disconnect()
            except Exception as err:
                _LOGGER.warning(f"exception while disconnecting client {err}")
            finally:
                await self._reset_async_state()
                self._reset_initialization()

        self.client = self._create_ge_client(event_loop=self.hass.loop)
        return self.client

    async def _async_start_client(self):
        """Start a new GeClient in the HASS event loop."""
        try:
            _LOGGER.debug("Creating and starting client")
            await self._get_client()
            await self._async_begin_session()
        except:
            _LOGGER.debug("could not start the client")
            self.client = None
            raise

    async def _async_begin_session(self):
        """Begins the ge_home session."""
        _LOGGER.debug("Beginning session")
        
        if self.client is None:
            raise HaInvalidOperation("Attempted to start a session without a valid client.")
        if self.hass is None or self.hass.loop is None:
            raise HaInvalidOperation("No running HASS loop to start client.")

        session = async_get_clientsession(self.hass)
        await self.client.async_get_credentials(session)

        fut = self.hass.loop.create_task(self.client.async_run_client())
        _LOGGER.debug("Client running")
        return fut

    def _reset_initialization(self):
        """ Reset synchronous state """

        #clear the client
        self.client = None  # type: Optional[GeWebsocketClient]

        # clear the appliances
        self._appliance_apis.clear()

        # Some record keeping to let us know when we can start generating entities
        self._got_roster = False
        self._init_done = False
        self._retry_count = 0
        self._reconnecting = False

    async def _reset_async_state(self):
        """ Reset asynchronous state """

        # Stop the polling task
        if self._updater_task:
            task = self._updater_task
            self._updater_task = None

            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass            
    
    #endregion

    #region Reconnection/Shutdown

    def _get_retry_delay(self) -> int:
        delay = MIN_RETRY_DELAY * 2 ** (self._retry_count - 1)
        return min(delay, MAX_RETRY_DELAY)

    @callback
    def _reconnect(self, log=False) -> None:
        """Prepare to reconnect ge_home session."""
        if log:
            _LOGGER.info("Will try to reconnect to ge_home service")
        if self.hass is None or self.hass.loop is None:
            raise HaInvalidOperation("No running HASS loop to reconnect client.")

        self.hass.loop.create_task(self._async_reconnect())

    async def _async_reconnect(self) -> None:
        """Try to reconnect ge_home session."""
        self._retry_count += 1
        _LOGGER.info(
            f"Attempting to reconnect to ge_home service (attempt {self._retry_count})"
        )

        try:
            async with async_timeout.timeout(CLIENT_START_ASYNC_TIMEOUT):
                await self._async_start_client()
        except Exception as err:
            _LOGGER.warning(f"Could not reconnect: {err}, will retry in {self._get_retry_delay()} seconds")
            self.hass.loop.call_later(self._get_retry_delay(), self._reconnect)
            _LOGGER.debug("Forcing a state refresh while disconnected")
            try:
                await self._refresh_ha_state()
            except Exception as err:
                _LOGGER.debug(f"Error refreshing state: {err}")

    @callback
    def _shutdown(self, event) -> None:
        """
        Close the connection on shutdown.
        Used as an argument to EventBus.async_listen_once.
        """
        _LOGGER.info("ge_home shutting down")

        #stop background polling
        self.hass.loop.create_task(self._reset_async_state())

        #if we have a client, disconnect it
        if self.client:
            self.client.clear_event_handlers()
            self.hass.loop.create_task(self.client.disconnect())

    #endregion

    #region Appliance Management

    def _is_appliance_valid(self, appliance: GeAppliance) -> bool:
        return appliance.appliance_type is not None

    def _get_appliance_api(self, appliance: GeAppliance) -> ApplianceApi:
        if appliance is None:
            return None

        self._dump_appliance(appliance)
        api_type = get_appliance_api_type(appliance.appliance_type or ErdApplianceType.UNKNOWN)
        return api_type(self, appliance)

    def _maybe_add_appliance_api(self, appliance: GeAppliance):
        mac_addr = appliance.mac_addr
        if mac_addr not in self.appliance_apis:
            _LOGGER.debug(f"Adding appliance api for appliance {mac_addr} ({appliance.appliance_type})")
            api = self._get_appliance_api(appliance)
            api.build_entities_list()
            self.appliance_apis[mac_addr] = api
        else:
            _LOGGER.debug(f"Already have appliance {mac_addr} ({appliance.appliance_type}), switching reference.")
            # if we already have the API, switch out its appliance reference for this one
            api = self.appliance_apis[mac_addr]
            api.appliance = appliance

    async def _async_maybe_trigger_all_ready(self):
        """See if we're all ready to go, and if so, let the games begin."""
        if self._init_done:
            _LOGGER.debug("Already initialized, cannot trigger ready.")
            # Been here, done this
            return
        
        if self.client is None:
            _LOGGER.warning("Client is already deallocated, cannot trigger ready.")
            return
                
        if self._got_roster and self.all_appliances_updated:
            _LOGGER.debug("Ready to go, sending ready signal!")
            self._init_done = True
            await self.client.async_event(EVENT_ALL_APPLIANCES_READY, None)
            async_dispatcher_send(
                self.hass, 
                self.signal_ready, 
                list(self.appliance_apis.values()))

    #endregion

    #region Background Updates

    async def _start_periodic_updates(self):

        if self._updater_task is not None and not self._updater_task.done():
            _LOGGER.debug("Polling already started, ignoring scheduling request.")
            return

        self._updater_task = self.hass.loop.create_task(self._request_periodic_updates())
        _LOGGER.debug("Scheduled background updater for execution.")

    async def _request_periodic_updates(self):
        """Periodic update loop."""

        _LOGGER.debug("Start requesting periodic updates.")

        try:
            while self.connected:
                await asyncio.sleep(UPDATE_INTERVAL)

                if (self.client is None or not self.connected or not self.client.available):
                    _LOGGER.debug(
                        f"Connection issue, cannot get update ("
                        f"client: { self.client is None },"
                        f"connected: { self.connected },"
                        f"available: { self.available }"
                    )
                    continue

                for api in self.appliance_apis.values():
                    try:
                        if api.appliance is None:
                            _LOGGER.debug(f"Appliance {api} is not valid, skipping update.")
                            continue

                        _LOGGER.debug(f"Requesting update for {api.appliance.mac_addr}")
                        await api.appliance.async_request_update()
                    except Exception as err:
                        _LOGGER.debug(f"Poll update failed for [{api.appliance.mac_addr}]: {err}")

        except asyncio.CancelledError:
            # Normal exit when shutting down
            pass

        _LOGGER.debug("Stopped requesting periodic updates.")         

    #endregion

    #region State Updates

    async def _refresh_ha_state(self):
        """ Performs a full refresh of all appliances """
        entities = [
            entity for api in self.appliance_apis.values() for entity in api.entities
        ]

        self._update_entity_state(entities)

    def _update_entity_state(self, entities: List[Entity]):
        """ Performs a refresh of the state for a list of entities """

        from .entities import GeEntity
        for entity in entities:
            # if this is a GeEntity, check if it's been added
            #if not, don't try to refresh this entity
            if isinstance(entity, GeEntity):
                gee: GeEntity = entity
                if not gee.added:
                    _LOGGER.debug(f"Entity {entity} ({entity.unique_id}, {entity.entity_id}) not yet added, skipping update...")
                    continue
            if entity.enabled:
                try:
                    _LOGGER.debug(f"Refreshing state for {entity} ({entity.unique_id}, {entity.entity_id}), state: {entity.state}")
                    entity.async_write_ha_state()
                except:
                    _LOGGER.warning(f"Could not refresh state for {entity} ({entity.unique_id}, {entity.entity_id}", exc_info=True)

    #endregion

    #region Debugging

    def _dump_appliance(self, appliance: GeAppliance, update_data: Optional[Dict[ErdCodeType, Any]] = None) -> None:
        if not _LOGGER.isEnabledFor(logging.DEBUG):
            return

        import pprint
        try:
            _LOGGER.debug(f"--- COMPREHENSIVE DUMP FOR APPLIANCE: {appliance.mac_addr} ---")
            appliance_data = {}            
            # dir() gets all attrs, including properties and methods
            for attr_name in dir(appliance):
                # skip "magic" methods and "private" attributes to reduce noise
                if attr_name.startswith('_'):
                    continue                
                try:
                    value = getattr(appliance, attr_name)
                    # for now skip methods - we only want data
                    if callable(value):
                        continue
                    appliance_data[attr_name] = value
                except Exception:
                    # some props might fail if called out of context
                    appliance_data[attr_name] = "Error: Could not read attribute"
            
            # add the internal property cache (i.e. current values)
            appliance_data["property_cache"] = appliance._property_cache

            # add the update data if available
            if update_data is not None:
                appliance_data["update_data"] = update_data
            
            _LOGGER.debug(pprint.pformat(appliance_data))
            _LOGGER.debug("--- END OF COMPREHENSIVE DUMP ---")
        except Exception as e:
            _LOGGER.error(f"Could not dump appliance {appliance}: {e}")

    #endregion

    #endregion
    
