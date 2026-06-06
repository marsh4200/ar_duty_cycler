"""The AR Duty Cycler integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .cycler import DutyCycler


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AR Duty Cycler from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    cycler = DutyCycler(hass, entry)
    await cycler.async_load()
    hass.data[DOMAIN][entry.entry_id] = cycler

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Entities are up; evaluate the engine (resume cycling if inside window).
    cycler.async_request_arm()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    cycler: DutyCycler = hass.data[DOMAIN][entry.entry_id]
    cycler.async_shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when the target entity / name is changed via options."""
    await hass.config_entries.async_reload(entry.entry_id)
