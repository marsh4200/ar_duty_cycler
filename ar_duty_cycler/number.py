"""Duration number entities for AR Duty Cycler."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .cycler import DutyCycler
from .entity import DutyCyclerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    cycler: DutyCycler = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            OnDurationNumber(cycler),
            OffDurationNumber(cycler),
        ]
    )


class _DurationNumber(DutyCyclerEntity, NumberEntity):
    _attr_native_min_value = 0.5
    _attr_native_max_value = 1440.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX


class OnDurationNumber(_DurationNumber):
    _attr_translation_key = "on_duration"
    _attr_icon = "mdi:timer-play-outline"

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "on_duration", "on_duration")

    @property
    def native_value(self) -> float:
        return self._cycler.on_min

    async def async_set_native_value(self, value: float) -> None:
        await self._cycler.async_set_on_min(value)


class OffDurationNumber(_DurationNumber):
    _attr_translation_key = "off_duration"
    _attr_icon = "mdi:timer-pause-outline"

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "off_duration", "off_duration")

    @property
    def native_value(self) -> float:
        return self._cycler.off_min

    async def async_set_native_value(self, value: float) -> None:
        await self._cycler.async_set_off_min(value)
