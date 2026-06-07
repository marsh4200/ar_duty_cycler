"""Window start/end time entities for AR Duty Cycler."""

from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
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
            WindowStartTime(cycler),
            WindowEndTime(cycler),
        ]
    )


class WindowStartTime(DutyCyclerEntity, TimeEntity):
    _attr_translation_key = "window_start"
    _attr_icon = "mdi:clock-start"

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "window_start", "window_start")

    @property
    def native_value(self) -> dt_time:
        return self._cycler.window_start

    async def async_set_value(self, value: dt_time) -> None:
        await self._cycler.async_set_window_start(value)


class WindowEndTime(DutyCyclerEntity, TimeEntity):
    _attr_translation_key = "window_end"
    _attr_icon = "mdi:clock-end"

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "window_end", "window_end")

    @property
    def native_value(self) -> dt_time:
        return self._cycler.window_end

    async def async_set_value(self, value: dt_time) -> None:
        await self._cycler.async_set_window_end(value)
