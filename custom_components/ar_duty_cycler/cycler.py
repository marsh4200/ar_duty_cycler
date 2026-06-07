"""Server-side duty-cycle engine for AR Duty Cycler.

One :class:`DutyCycler` instance exists per config entry. It owns the live,
adjustable state (durations, window times, park state, master enable) and
drives the target entity on/off on a repeating cycle, but only while inside
the configured daily time window. The cycle runs entirely on the HA event
loop, so it keeps working whether or not any dashboard is open.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time as dt_time, timedelta

from homeassistant.const import (
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

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
    PHASE_OFF,
    PHASE_ON,
    SIGNAL_UPDATE,
    STATUS_IDLE,
    STATUS_RUNNING_OFF,
    STATUS_RUNNING_ON,
    STATUS_WAITING,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

HA_DOMAIN = "homeassistant"


def _parse_time(value) -> dt_time:
    """Parse a 'HH:MM' / 'HH:MM:SS' string (or pass through a time) to time."""
    if isinstance(value, dt_time):
        return value
    parsed = dt_util.parse_time(str(value))
    return parsed or _parse_time(DEFAULT_WINDOW_START)


def _fmt_time(value: dt_time) -> str:
    return value.strftime("%H:%M:%S")


class DutyCycler:
    """Drives a target entity on/off on a repeating cycle within a time window."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.hass = hass
        self.entry = entry
        self._store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")

        self.target_entity: str = entry.data[CONF_TARGET_ENTITY]
        self.name: str = entry.data.get(CONF_NAME) or entry.title

        # Live, adjustable state (defaults; replaced by stored/seeded values).
        self.enabled: bool = False
        self.on_min: float = DEFAULT_ON_DURATION
        self.off_min: float = DEFAULT_OFF_DURATION
        self.window_start: dt_time = _parse_time(DEFAULT_WINDOW_START)
        self.window_end: dt_time = _parse_time(DEFAULT_WINDOW_END)
        self.park_state: str = DEFAULT_PARK_STATE
        self.start_phase: str = DEFAULT_START_PHASE

        # Runtime.
        self.status: str = STATUS_IDLE
        self.phase: str | None = None
        self._phase_started: datetime | None = None
        self._timer_unsub = None
        self._lock = asyncio.Lock()

        # Populated by entities as they are added; consumed by the card.
        self.entity_ids: dict[str, str] = {"target": self.target_entity}

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    async def async_load(self) -> None:
        data = await self._store.async_load()
        if data is None:
            opts = {**self.entry.data, **self.entry.options}
            self.on_min = float(opts.get(CONF_ON_DURATION, DEFAULT_ON_DURATION))
            self.off_min = float(opts.get(CONF_OFF_DURATION, DEFAULT_OFF_DURATION))
            self.window_start = _parse_time(
                opts.get(CONF_WINDOW_START, DEFAULT_WINDOW_START)
            )
            self.window_end = _parse_time(
                opts.get(CONF_WINDOW_END, DEFAULT_WINDOW_END)
            )
            self.park_state = opts.get(CONF_PARK_STATE, DEFAULT_PARK_STATE)
            self.start_phase = opts.get(CONF_START_PHASE, DEFAULT_START_PHASE)
            self.enabled = False
            await self._store.async_save(self._as_dict())
        else:
            self.enabled = bool(data.get("enabled", False))
            self.on_min = float(data.get("on_min", DEFAULT_ON_DURATION))
            self.off_min = float(data.get("off_min", DEFAULT_OFF_DURATION))
            self.window_start = _parse_time(
                data.get("window_start", DEFAULT_WINDOW_START)
            )
            self.window_end = _parse_time(data.get("window_end", DEFAULT_WINDOW_END))
            self.park_state = data.get("park_state", DEFAULT_PARK_STATE)
            self.start_phase = data.get("start_phase", DEFAULT_START_PHASE)

    def _as_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "on_min": self.on_min,
            "off_min": self.off_min,
            "window_start": _fmt_time(self.window_start),
            "window_end": _fmt_time(self.window_end),
            "park_state": self.park_state,
            "start_phase": self.start_phase,
        }

    async def _persist(self) -> None:
        await self._store.async_save(self._as_dict())
        self._notify()

    @callback
    def _notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(self.entry.entry_id))

    # ------------------------------------------------------------------ #
    # Setters used by the entity platforms
    # ------------------------------------------------------------------ #
    async def async_set_enabled(self, value: bool) -> None:
        self.enabled = bool(value)
        if not self.enabled:
            self.phase = None
        await self._persist()
        await self._arm()

    async def async_set_on_min(self, value: float) -> None:
        self.on_min = float(value)
        await self._persist()
        await self._arm()

    async def async_set_off_min(self, value: float) -> None:
        self.off_min = float(value)
        await self._persist()
        await self._arm()

    async def async_set_window_start(self, value: dt_time) -> None:
        self.window_start = value
        await self._persist()
        await self._arm()

    async def async_set_window_end(self, value: dt_time) -> None:
        self.window_end = value
        await self._persist()
        await self._arm()

    async def async_set_park_state(self, value: str) -> None:
        self.park_state = value
        await self._persist()
        await self._arm()

    async def async_set_start_phase(self, value: str) -> None:
        self.start_phase = value
        await self._persist()
        # Changing the start phase only matters at the next window start; no
        # need to disturb a cycle already in progress.
        self._notify()

    # ------------------------------------------------------------------ #
    # Scheduling core
    # ------------------------------------------------------------------ #
    @callback
    def async_request_arm(self) -> None:
        """Schedule an (re)evaluation of the engine on the event loop."""
        self.hass.async_create_task(self._arm())

    async def _arm(self) -> None:
        async with self._lock:
            self._cancel_timer()
            now = dt_util.now()

            if not self.enabled:
                self._set_status(STATUS_IDLE)
                return

            if not self._in_window(now):
                # Card is "on" but outside its window: park the target in the
                # chosen safe state and wait for the next window start.
                self.phase = None
                await self._apply(self.park_state == PHASE_ON)
                self._set_status(STATUS_WAITING)
                self._schedule(self._next_window_start(now))
                return

            # Inside the window: run the cycle.
            if self.phase is None:
                self.phase = self.start_phase
                self._phase_started = now

            await self._apply(self.phase == PHASE_ON)
            self._set_status(
                STATUS_RUNNING_ON if self.phase == PHASE_ON else STATUS_RUNNING_OFF
            )

            dur = self.on_min if self.phase == PHASE_ON else self.off_min
            phase_end = (self._phase_started or now) + timedelta(minutes=dur)
            win_end = self._window_end_dt(now)
            nxt = min(phase_end, win_end)
            if nxt <= now:
                nxt = now + timedelta(seconds=1)
            self._schedule(nxt)

    @callback
    def _on_timer(self, _now) -> None:
        self._timer_unsub = None
        self.hass.async_create_task(self._handle_timer())

    async def _handle_timer(self) -> None:
        now = dt_util.now()
        if self.enabled and self._in_window(now):
            # End of a phase, still inside window -> flip.
            self.phase = PHASE_OFF if self.phase == PHASE_ON else PHASE_ON
            self._phase_started = now
        else:
            # Window closed (or disabled) while running -> park.
            self.phase = None
        await self._arm()

    def _schedule(self, when: datetime) -> None:
        self._cancel_timer()
        self._timer_unsub = async_track_point_in_time(self.hass, self._on_timer, when)

    def _cancel_timer(self) -> None:
        if self._timer_unsub is not None:
            self._timer_unsub()
            self._timer_unsub = None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    async def _apply(self, on: bool) -> None:
        service = SERVICE_TURN_ON if on else SERVICE_TURN_OFF
        await self.hass.services.async_call(
            HA_DOMAIN, service, {"entity_id": self.target_entity}, blocking=False
        )

    def _set_status(self, status: str) -> None:
        if status != self.status:
            self.status = status
        self._notify()

    def _in_window(self, now: datetime) -> bool:
        t = now.time()
        s, e = self.window_start, self.window_end
        if s == e:
            return False
        if s < e:
            return s <= t < e
        # Overnight window (e.g. 22:00 -> 06:00).
        return t >= s or t < e

    def _next_window_start(self, now: datetime) -> datetime:
        candidate = now.replace(
            hour=self.window_start.hour,
            minute=self.window_start.minute,
            second=self.window_start.second,
            microsecond=0,
        )
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    def _window_end_dt(self, now: datetime) -> datetime:
        end = now.replace(
            hour=self.window_end.hour,
            minute=self.window_end.minute,
            second=self.window_end.second,
            microsecond=0,
        )
        if self.window_start < self.window_end:
            if end <= now:
                end += timedelta(days=1)  # safety
            return end
        # Overnight window.
        if now.time() >= self.window_start:
            end += timedelta(days=1)
        return end

    @callback
    def async_shutdown(self) -> None:
        self._cancel_timer()
