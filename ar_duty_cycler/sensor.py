"""Status sensor for AR Duty Cycler."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, STATUS_OPTIONS
from .cycler import DutyCycler
from .entity import DutyCyclerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    cycler: DutyCycler = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StatusSensor(cycler)])


class StatusSensor(DutyCyclerEntity, SensorEntity):
    _attr_translation_key = "status"
    _attr_icon = "mdi:state-machine"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUS_OPTIONS

    def __init__(self, cycler: DutyCycler) -> None:
        super().__init__(cycler, "status", "status")

    @property
    def native_value(self) -> str:
        return self._cycler.status

    @property
    def extra_state_attributes(self) -> dict:
        return {"current_phase": self._cycler.phase}
