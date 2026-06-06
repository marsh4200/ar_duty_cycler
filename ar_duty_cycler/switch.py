"""Master enable switch for AR Duty Cycler."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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
    async_add_entities([CyclerEnableSwitch(cycler)])


class CyclerEnableSwitch(DutyCyclerEntity, SwitchEntity):
    """Turns the whole cycler on/off (the 'card on/off')."""

    _attr_translation_key = "enable"
    _attr_icon = "mdi:autorenew"

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "enable", "enable")

    @property
    def is_on(self) -> bool:
        return self._cycler.enabled

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "cycler_entities": dict(self._cycler.entity_ids),
            "status": self._cycler.status,
            "current_phase": self._cycler.phase,
            "target_entity": self._cycler.target_entity,
        }

    async def async_turn_on(self, **kwargs) -> None:
        await self._cycler.async_set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._cycler.async_set_enabled(False)
