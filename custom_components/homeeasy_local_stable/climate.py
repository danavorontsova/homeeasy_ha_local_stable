"""Climate platform for Home Easy HVAC Local - Stable Version."""
from typing import List
import logging

from homeeasy.DeviceState import Mode, FanMode, HorizontalFlowMode, VerticalFlowMode
from homeeasy.HomeEasyLib import HomeEasyLib, DeviceState

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import DOMAIN, ICON, CLIMATE
from .entity import Entity

_LOGGER = logging.getLogger(__name__)

SUPPORT_FAN = ["Auto", "Lowest", "Low", "Mid-low", "Mid-high", "High", "Highest", "Quite", "Turbo"]
SUPPORT_HVAC = [HVACMode.OFF, HVACMode.AUTO, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.HEAT]

HA_STATE_TO_MODE_MAP = {
    HVACMode.AUTO: Mode.Auto,
    HVACMode.COOL: Mode.Cool,
    HVACMode.DRY: Mode.Dry,
    HVACMode.FAN_ONLY: Mode.Fan,
    HVACMode.HEAT: Mode.Heat,
}

MODE_TO_HA_STATE_MAP = {value: key for key, value in HA_STATE_TO_MODE_MAP.items()}

SWING_MODES = {
    "Stop": (HorizontalFlowMode.Stop, VerticalFlowMode.Stop),
    "Horizontal": (HorizontalFlowMode.Swing, VerticalFlowMode.Stop),
    "Vertical": (HorizontalFlowMode.Stop, VerticalFlowMode.Swing),
    "Both": (HorizontalFlowMode.Swing, VerticalFlowMode.Swing),
    "Custom": (HorizontalFlowMode.Stop, VerticalFlowMode.Stop),
}

async def async_setup_entry(hass, entry, async_add_devices):
    """Setup climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([HomeEasyHvacLocal(coordinator, entry)])

class HomeEasyHvacLocal(Entity, ClimateEntity):
    """Home Easy Local climate class with stability fixes."""

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def available(self) -> bool:
        """Перевірка доступності: якщо координатор не має даних, пристрій недоступний."""
        return self.coordinator.last_update_success and self.coordinator.state is not None

    @property
    def supported_features(self) -> int:
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.SWING_MODE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON

    @property
    def name(self) -> str:
        return f"{super().name}_{CLIMATE}"

    @property
    def temperature_unit(self) -> str:
        if self.coordinator.state is None or not self.coordinator.state.temperatureScale:
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self) -> float:
        if self.coordinator.state is None:
            return None
        return self.coordinator.state.indoorTemperature

    @property
    def target_temperature(self) -> float:
        if self.coordinator.state is None:
            return None
        return self.coordinator.state.desiredTemperature

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None or self.coordinator.state is None:
            return
        state = self.coordinator.state
        state.desiredTemperature = temperature
        # Додаємо спробу відправки з обробкою помилки
        try:
            await self.coordinator.send(state)
        except Exception as e:
            _LOGGER.error("Failed to set temperature: %s", e)

    @property
    def target_temperature_step(self) -> float:
        return 1

    @property
    def min_temp(self) -> float:
        return 16

    @property
    def max_temp(self) -> float:
        return 31

    @property
    def hvac_mode(self) -> str:
        if self.coordinator.state is None or not self.coordinator.state.power:
            return HVACMode.OFF 
        return MODE_TO_HA_STATE_MAP.get(self.coordinator.state.mode, HVACMode.AUTO)

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        if self.coordinator.state is None:
            return
        state = self.coordinator.state
        if hvac_mode == HVACMode.OFF:
            state.power = False
        else:
            state.power = True
            state.mode = HA_STATE_TO_MODE_MAP[hvac_mode]
        await self.coordinator.send(state)

    @property
    def hvac_modes(self):
        return SUPPORT_HVAC

    @property
    def fan_mode(self) -> str:
        if self.coordinator.state is None:
            return SUPPORT_FAN[0]
        try:
            mode = int(self.coordinator.state.fanMode)
            return SUPPORT_FAN[mode]
        except (ValueError, IndexError):
            return SUPPORT_FAN[0]

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if self.coordinator.state is None:
            return
        index = SUPPORT_FAN.index(fan_mode)
        state = self.coordinator.state
        state.fanMode = FanMode(index)
        await self.coordinator.send(state)

    @property
    def fan_modes(self) -> List[str]:
        return SUPPORT_FAN

    @property
    def swing_mode(self) -> str:
        if self.coordinator.state is None:
            return list(SWING_MODES.keys())[0]

        for (key, value) in SWING_MODES.items():
            h, v = value
            if h == self.coordinator.state.flowHorizontalMode and v == self.coordinator.state.flowVerticalMode:
                return key
        return list(SWING_MODES.keys())[0]

    @property
    def swing_modes(self) -> List[str]:
        return list(SWING_MODES.keys())

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        if self.coordinator.state is None:
            return
        h, v = SWING_MODES[swing_mode]
        state = self.coordinator.state
        state.flowHorizontalMode = h
        state.flowVerticalMode = v
        await self.coordinator.send(state)
