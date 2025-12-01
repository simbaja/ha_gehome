"""Data update coordinator for GE Home (SmartHQ) Appliances"""

import asyncio
from contextlib import suppress
import random
import logging
import time
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, List

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_REGION
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
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
    ErdApplianceType,
    GeClientState
)
from gehomesdk import GeAuthFailedError, GeGeneralServerError, GeNotAuthenticatedError

from .const import *
from .devices import ApplianceApi, get_appliance_api_type
from .exceptions import HaAuthError, HaCannotConnect

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

        self._client : GeWebsocketClient | None = None
        self._config_entry = config_entry
        self._username = config_entry.data[CONF_USERNAME]
        self._password = config_entry.data[CONF_PASSWORD]
        self._region = config_entry.data[CONF_REGION]
        self._appliance_apis: Dict[str, ApplianceApi] = {}
        self._signal_remove_callbacks: List[Callable] = []
        self._got_roster = False
        self._init_done = False
        self._all_initial_updates_received = asyncio.Event()

        self._updater_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._last_persistent_log: float = 0.0
        self._retry_count: int = 0
        self._last_ha_refresh: float = 0.0

        self._reset_sync_state()

    #region Public Properties

    @property
    def appliances(self) -> Iterable[GeAppliance]:
        if self._client is None:
            return []

        return self._client.appliances.values()

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
        return self._client is not None and self._client.connected
    
    @property
    def available(self) -> bool:
        """
        Indicates whether the coordinator is available
        """
        return self._client is not None and self._client.available
    
    #endregion

    #region Public Methods

    def add_signal_remove_callback(self, cb: Callable):
        self._signal_remove_callbacks.append(cb)

    async def async_setup(self):
        """Setup a new coordinator"""
        _LOGGER.debug("Setting up the coordinator")

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

    async def async_reset(self) -> bool:
        """Resets the coordinator."""
        _LOGGER.debug("Resetting the coordinator")
        entry = self._config_entry

        # stop the client
        await self._async_stop_client()
        
        # remove all the callbacks for this coordinator
        for c in self._signal_remove_callbacks:
            c()
        self._signal_remove_callbacks.clear()

        # cancel the notification
        try:
            persistent_notification.async_dismiss(self.hass, CONNECTION_NOTIFICATION_ID)
        except Exception:
            pass

        # unload
        unload_ok = await self.hass.config_entries.async_unload_platforms(
            self._config_entry, PLATFORMS
        )
        return unload_ok

    @callback
    def shutdown(self, event) -> None:
        """
        Close the connection on shutdown.
        Used as an argument to EventBus.async_listen_once.
        """
        _LOGGER.info("ge_home shutting down")

        #stop the client and existing background tasks
        self.hass.loop.create_task(self._async_stop_client())

    #endregion    
                  
    #region Internal Methods

    #region Initialization/Reset/Shutdown

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
        client.add_event_handler(EVENT_APPLIANCE_INITIAL_UPDATE, self._on_device_initial_update)
        client.add_event_handler(EVENT_APPLIANCE_UPDATE_RECEIVED, self._on_device_update)
        client.add_event_handler(EVENT_GOT_APPLIANCE_LIST, self._on_appliance_list)
        client.add_event_handler(EVENT_DISCONNECTED, self._on_disconnect)
        client.add_event_handler(EVENT_CONNECTED, self._on_connect)
        return client
    
    async def _async_start_client(self) -> None:
        """
        Tear down old client if present, reset state, and create & start a fresh client.
        """

        # Teardown old client if present
        await self._async_stop_client()

        # Create new client and start it
        try:
            self._client = self._create_ge_client(event_loop=self.hass.loop)
            session = async_get_clientsession(self.hass)
            await self._client.async_get_credentials(session)
        except Exception as err:
            _LOGGER.error(f"could not start the client: {err}")
            self._client = None
            raise

        # Start the client run loop
        self.hass.loop.create_task(self._client.async_run_client())
        _LOGGER.debug("Scheduled the client for execution.")

    async def _async_stop_client(self):
        """ Teardown the client if it exists """
        if self._client:
            try:
                self._client.clear_event_handlers()
                await self._client.disconnect()
            except Exception as err:
                _LOGGER.warning("Error disconnecting client: %s", err)
            finally:
                self._client = None

        # Reset asynchronous and synchronous states
        await self._async_reset_state()
        self._reset_sync_state()

    def _reset_sync_state(self):
        """ Reset synchronous state """

        # clear the appliances
        self._appliance_apis.clear()

        # reset the initialization
        self._all_initial_updates_received.clear()

        # Some record keeping to let us know when we can start generating entities
        self._got_roster = False
        self._init_done = False
        self._retry_count = 0

    async def _async_reset_state(self):
        """ Reset asynchronous state """

        await self._stop_periodic_updates()
        await self._stop_reconnect_worker()

    #endregion

    #region Reconnection Lifecycle

    async def _ensure_client_running(self) -> None:
        if self._client is None or self._client.state == GeClientState.DISCONNECTED:
            _LOGGER.debug("Client missing or disconnected, starting new client")
            await self._async_start_client()

    async def _start_reconnect_worker(self) -> None:
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = self.hass.loop.create_task(self._reconnect_worker())

    async def _stop_reconnect_worker(self) -> None:
        self._retry_count = 0
        self._last_persistent_log = 0.0
        if self._reconnect_task:
            self._reconnect_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._reconnect_task
            self._reconnect_task = None
        try:
            persistent_notification.async_dismiss(self.hass, CONNECTION_NOTIFICATION_ID)
        except Exception:
            pass            

    async def _reconnect_worker(self) -> None:
        _LOGGER.debug("Reconnect worker started")
        try:
            while True:
                if self._client and self._client.state != GeClientState.DISCONNECTED:
                    _LOGGER.debug("Client no longer disconnected, exiting worker")
                    return

                self._retry_count += 1
                sleep_time = self._get_retry_delay()

                _LOGGER.info(f"Retrying in {sleep_time:.1f}s (attempt {self._retry_count})")
                await asyncio.sleep(sleep_time)

                if self._client and self._client.state != GeClientState.DISCONNECTED:
                    _LOGGER.debug("Client became healthy before retry, exiting")
                    return

                try:
                    await self._async_start_client()
                except (GeNotAuthenticatedError, GeAuthFailedError):
                    self._show_persistent_notification("Authentication failure: please re-authenticate the GE Home integration.")
                    return
                except Exception as err:
                    _LOGGER.warning(f"Reconnect attempt failed: {err}")

                if self._client and self._client.state != GeClientState.DISCONNECTED:
                    return

                if self._retry_count >= NOTIFY_AFTER_RETRIES:
                    self._show_notification_once_per_interval(
                        title="GE Home: connection issues",
                        message=f"Unable to connect after {self._retry_count} attempts. Will continue retrying automatically.",
                        interval=PERSISTENT_RETRY_LOG_INTERVAL,
                    )
                await self._throttled_refresh_ha_state()
        except asyncio.CancelledError:
            _LOGGER.debug("Reconnect worker cancelled, ignoring.")
        finally:
            if self._reconnect_task and self._reconnect_task.done():
                self._reconnect_task = None

    def _get_retry_delay(self) -> float:
        delay = float(min(MIN_RETRY_DELAY * (2 ** self._retry_count), MAX_RETRY_DELAY))
        jitter = delay * RECONNECT_JITTER * (random.random() * 2 - 1)
        return delay + jitter

    #endregion

    #region Persistent Notifications

    def _show_persistent_notification(self, message: str, title: str = "GE Home Connection"):
        try:
            persistent_notification.async_create(self.hass, message, title, notification_id=CONNECTION_NOTIFICATION_ID)
        except Exception:
            _LOGGER.exception("Failed to create persistent notification")

    def _show_notification_once_per_interval(self, title: str, message: str, interval: int = 300):
        now = time.time()
        if now - self._last_persistent_log > interval:
            self._last_persistent_log = now
            self._show_persistent_notification(message, title)    

    #endregion

    #region Client Event Handlers

    async def _on_device_update(self, data: Tuple[GeAppliance, Dict[ErdCodeType, Any]]):
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

    async def _on_appliance_list(self, _):
        """When we get an appliance list, mark it and maybe trigger all ready."""

        _LOGGER.debug("Got roster update")
        self.last_update_success = True
        if not self._got_roster:
            self._got_roster = True

        try:
            await asyncio.wait_for(self._all_initial_updates_received.wait(), timeout=INITIAL_UPDATE_TIMEOUT)
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout waiting for initial appliance updates")
        finally:
            # Remove stale devices/entities after everything is ready
            await self._async_remove_stale_devices()

            # Trigger all-ready signal            
            await self._async_maybe_trigger_all_ready(True)

    async def _on_device_initial_update(self, appliance: GeAppliance):
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

    async def _on_disconnect(self, _):
        """Handle disconnection."""
        _LOGGER.debug(f"Client has been disconnected, starting reconnection attempts.")
        self.last_update_success = False
        await self._start_reconnect_worker()

    async def _on_connect(self, _):
        """Set state upon connection."""
        self.last_update_success = True
        await self._stop_reconnect_worker()

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

    def _maybe_add_appliance_api(self, appliance: GeAppliance) -> None:
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

    async def _async_maybe_trigger_all_ready(self, force: bool = False) -> None:
        """See if we're all ready to go, and if so, let the games begin."""
        if self._init_done:
            # Been here, done this            
            _LOGGER.debug("Already initialized, cannot trigger ready.")
            return
        
        if self._client is None:
            _LOGGER.warning("Client is already deallocated, cannot trigger ready.")
            return
                
        if force or (self._got_roster and self.all_appliances_updated):
            _LOGGER.debug("Ready to go, sending ready signal!")
            self._init_done = True
            self._all_initial_updates_received.set()

            await self._client.async_event(EVENT_ALL_APPLIANCES_READY, None)
            async_dispatcher_send(
                self.hass, 
                self.signal_ready, 
                list(self.appliance_apis.values()))
            
    async def _async_remove_stale_devices(self):
        """Remove devices/entities from HA that no longer exist in the cloud."""
        if self._client is None:
            return

        # Device and entity registries
        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)

        # MAC addresses of all currently valid appliances
        current_macs = set(self._appliance_apis.keys())

        # Loop through all devices for this config entry
        for device_entry in list(device_registry.devices.values()):
            # Skip devices not associated with this config entry
            if self._config_entry.entry_id not in device_entry.config_entries:
                continue

            # Extract mac_addresses (assumes identifiers contain ("ge_home", mac))
            device_mac = None
            for ident in device_entry.identifiers:
                if ident[0] == DOMAIN:  # DOMAIN = "ge_home"
                    device_mac = ident[1]
                    break

            if device_mac and device_mac not in current_macs:
                _LOGGER.info(f"Removing stale device {device_entry.name} ({device_mac}) from HA registry")

                # Remove all entities linked to this device
                for entity_entry in list(entity_registry.entities.values()):
                    if entity_entry.device_id == device_entry.id:
                        entity_registry.async_remove(entity_entry.entity_id)

                # Remove the device itself
                device_registry.async_remove_device(device_entry.id)            

    #endregion

    #region Background Updates

    async def _start_periodic_updates(self):

        if self._updater_task is not None and not self._updater_task.done():
            _LOGGER.debug("Polling already started, ignoring scheduling request.")
            return

        self._updater_task = self.hass.loop.create_task(self._request_periodic_updates())
        _LOGGER.debug("Scheduled background updater for execution.")

    async def _stop_periodic_updates(self) -> None:
        if self._updater_task:
            self._updater_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._updater_task
            self._updater_task = None        

    async def _request_periodic_updates(self):
        """Periodic update loop."""

        _LOGGER.debug("Start requesting periodic updates.")

        try:
            while self.connected:
                await asyncio.sleep(STATE_UPDATE_INTERVAL)

                if (self._client is None or not self.connected or not self._client.available):
                    _LOGGER.debug(
                        f"Connection issue, cannot get update ("
                        f"client: { self._client is None },"
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

    async def _throttled_refresh_ha_state(self):
        now = time.time()
        if now - self._last_ha_refresh > HA_REFRESH_INTERVAL:
            try:
                await self._refresh_ha_state()
            except Exception:
                _LOGGER.debug("Error refreshing HA state during reconnect", exc_info=True)
            finally:
                self._last_ha_refresh = now

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
    
