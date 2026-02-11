"""Custom integration to integrate Home Easy compatible HVAC with Home Assistant."""
from homeassistant.helpers.debounce import Debouncer
from homeeasy.DeviceState import DeviceState
from homeeasy.HomeEasyLibLocal import HomeEasyLibLocal
from datetime import timedelta
import logging
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_IP,
    DOMAIN,
)

# Збільшуємо інтервал, щоб не перевантажувати модуль
SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER: logging.Logger = logging.getLogger(__package__)

class UpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API with auto-reconnect."""

    state: DeviceState = None

    def __init__(self, hass: HomeAssistant, ip: str) -> None:
        """Initialize."""
        self._ip = ip
        # Передаємо колбек для оновлення даних
        self._api = HomeEasyLibLocal(hass.loop, self._update_callback)
        self.platforms = []
        self._connected = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            # Оптимізуємо дебаунсер для швидкого відгуку на команди
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=2.0, 
                immediate=True,
                function=self.async_refresh,
            ),
        )

    async def _async_update_data(self):
        """Update data via library with connection health check."""
        try:
            # Якщо зв'язок втрачено, пробуємо підключитися з таймаутом
            if not self._connected:
                _LOGGER.debug("Connecting to AC at %s", self._ip)
                await asyncio.wait_for(self._api.connect(self._ip), timeout=10.0)
                self._connected = True

            # Запит статусу
            await asyncio.wait_for(self._api.request_status_async(), timeout=5.0)
            
        except (asyncio.TimeoutError, Exception) as err:
            self._connected = False # Скидаємо статус, щоб наступного разу був реконнект
            _LOGGER.warning("AC connection error at %s: %s. Will retry.", self._ip, err)
            # Не викидаємо UpdateFailed відразу, щоб не "сіріли" кнопки миттєво
            return self.state

    async def _update_callback(self, state):
        """Callback from library when new data arrives."""
        if state is not None:
            self.state = state
            self.async_set_updated_data(state)

    async def send(self, state):
        """Send state to device with error handling."""
        try:
            await self._api.send(state)
            # Після відправки команди відразу просимо оновити дані
            await self.async_request_refresh()
        except Exception as e:
            self._connected = False
            _LOGGER.error("Error sending command to AC: %s", e)
