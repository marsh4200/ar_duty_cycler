"""Park-state and start-phase select entities for AR Duty Cycler."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, STATE_OPTIONS
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
            ParkStateSelect(cycler),
            StartPhaseSelect(cycler),
        ]
    )


class ParkStateSelect(DutyCyclerEntity, SelectEntity):
    """State the target is forced into when the window closes."""

    _attr_translation_key = "park_state"
    _attr_icon = "mdi:home-export-outline"
    _attr_options = STATE_OPTIONS

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "park_state", "park_state")

    @property
    def current_option(self) -> str:
        return self._cycler.park_state

    async def async_select_option(self, option: str) -> None:
        await self._cycler.async_set_park_state(option)


class StartPhaseSelect(DutyCyclerEntity, SelectEntity):
    """Whether the cycle begins in the ON or OFF phase at window start."""

    _attr_translation_key = "start_phase"
    _attr_icon = "mdi:flag-checkered"
    _attr_options = STATE_OPTIONS
    _attr_entity_registry_enabled_default = True

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "start_phase", "start_phase")

    @property
    def current_option(self) -> str:
        return self._cycler.start_phase

    async def async_select_option(self, option: str) -> None:
        await self._cycler.async_set_start_phase(option)
