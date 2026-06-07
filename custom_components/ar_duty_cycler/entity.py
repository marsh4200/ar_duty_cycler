"""Base entity for AR Duty Cycler."""

from __future__ import annotations

from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN, MANUFACTURER, MODEL, SIGNAL_UPDATE
from .cycler import DutyCycler


class DutyCyclerEntity(Entity):
    """Common plumbing for all duty-cycler entities."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, cycler: DutyCycler, role: str, unique_suffix: str) -> None:
        self._cycler = cycler
        self._role = role
        self._attr_unique_id = f"{cycler.entry.entry_id}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cycler.entry.entry_id)},
            name=cycler.name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        # Register this entity_id so the master switch can advertise the full
        # set to the Lovelace card for auto-discovery.
        self._cycler.entity_ids[self._role] = self.entity_id
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE.format(self._cycler.entry.entry_id),
                self.async_write_ha_state,
            )
        )
        # Nudge siblings so the switch refreshes its attribute map.
        async_dispatcher_send(
            self.hass, SIGNAL_UPDATE.format(self._cycler.entry.entry_id)
        )
