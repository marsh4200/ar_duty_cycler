"""Config flow for AR Duty Cycler."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_NAME,
    CONF_OFF_DURATION,
    CONF_ON_DURATION,
    CONF_PARK_STATE,
    CONF_START_PHASE,
    CONF_TARGET_ENTITY,
    CONF_WINDOW_END,
    CONF_WINDOW_START,
    DEFAULT_OFF_DURATION,
    DEFAULT_ON_DURATION,
    DEFAULT_PARK_STATE,
    DEFAULT_START_PHASE,
    DEFAULT_WINDOW_END,
    DEFAULT_WINDOW_START,
    DOMAIN,
    STATE_OPTIONS,
)

_DURATION_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0.5, max=1440, step=0.5, unit_of_measurement="min", mode="box"
    )
)
_TIME_SELECTOR = selector.TimeSelector()
_STATE_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=STATE_OPTIONS,
        translation_key="state_choice",
        mode=selector.SelectSelectorMode.DROPDOWN,
    )
)
_ENTITY_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["switch", "light", "input_boolean", "fan"])
)


def _data_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
            vol.Required(
                CONF_TARGET_ENTITY, default=defaults.get(CONF_TARGET_ENTITY)
            ): _ENTITY_SELECTOR,
            vol.Required(
                CONF_ON_DURATION,
                default=defaults.get(CONF_ON_DURATION, DEFAULT_ON_DURATION),
            ): _DURATION_SELECTOR,
            vol.Required(
                CONF_OFF_DURATION,
                default=defaults.get(CONF_OFF_DURATION, DEFAULT_OFF_DURATION),
            ): _DURATION_SELECTOR,
            vol.Required(
                CONF_WINDOW_START,
                default=defaults.get(CONF_WINDOW_START, DEFAULT_WINDOW_START),
            ): _TIME_SELECTOR,
            vol.Required(
                CONF_WINDOW_END,
                default=defaults.get(CONF_WINDOW_END, DEFAULT_WINDOW_END),
            ): _TIME_SELECTOR,
            vol.Required(
                CONF_PARK_STATE,
                default=defaults.get(CONF_PARK_STATE, DEFAULT_PARK_STATE),
            ): _STATE_SELECTOR,
            vol.Required(
                CONF_START_PHASE,
                default=defaults.get(CONF_START_PHASE, DEFAULT_START_PHASE),
            ): _STATE_SELECTOR,
        }
    )


class ARDutyCyclerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )
        return self.async_show_form(
            step_id="user", data_schema=_data_schema({}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ARDutyCyclerOptionsFlow()


class ARDutyCyclerOptionsFlow(OptionsFlow):
    """Allow changing the target entity / name after setup.

    Durations, window times, park and start phase are adjusted live via the
    device's own entities, so they are intentionally not re-edited here.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=data, title=data[CONF_NAME]
            )
            return self.async_create_entry(title="", data={})

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, default=self.config_entry.data.get(CONF_NAME)
                ): str,
                vol.Required(
                    CONF_TARGET_ENTITY,
                    default=self.config_entry.data.get(CONF_TARGET_ENTITY),
                ): _ENTITY_SELECTOR,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
