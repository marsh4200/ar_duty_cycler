# AR Duty Cycler

A Home Assistant custom integration that cycles an entity **ON / OFF on repeat**
inside a daily **time window**, then parks it in a chosen safe state when the
window closes. Built for things like electric blankets, heaters, pumps, fogger
foggers, anything you want pulsed for a stretch of the day.

The cycle runs **server-side on the HA event loop** — it keeps ticking whether
or not a dashboard is open. The Lovelace card is just a control surface on top.

---

## What it does

When you turn the cycle **on** (master switch), nothing happens until the
**window start** time. At that point it begins the loop:

```
ON  (on-duration)  →  OFF (off-duration)  →  ON  →  OFF  →  …
```

…repeating until the **window end** time. When the window closes it stops and
forces the target into your chosen **park state** (ON or OFF) so it can never be
left stranded in the wrong phase. Next day at the start time it re-arms
automatically.

Everything is live-adjustable from the card or the entities — durations, window
times, park state, and which phase the cycle starts in.

### Example — electric blanket

- ON duration: `10 min`, OFF duration: `10 min`
- Window: `17:00 → 22:00`
- Start phase: `on`
- When window closes: `off`

At 17:00 the blanket turns on for 10 min, off for 10 min, on, off… through to
22:00, where it's forced off and stays off until the next day.

---

## Install

### Manual / HACS-custom-repo

1. Copy `custom_components/ar_duty_cycler/` into your HA `config/custom_components/` folder.
2. Restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → AR Duty Cycler.**
4. Pick the entity to cycle and set your initial durations / window / states.

You can add as many instances as you like — one per device. Each creates its own
HA device with these entities:

| Entity | Role |
|---|---|
| `switch.<name>_cycle` | Master enable (the "card on/off") |
| `number.<name>_on_duration` | ON minutes |
| `number.<name>_off_duration` | OFF minutes |
| `time.<name>_window_start` | Window start |
| `time.<name>_window_end` | Window end |
| `select.<name>_state_when_closed` | Park state at window end |
| `select.<name>_start_phase` | Phase at window start |
| `sensor.<name>_status` | `idle` / `waiting` / `running_on` / `running_off` |

### Card

1. Copy `ar-duty-cycler-card.js` into `config/www/`.
2. **Settings → Dashboards → ⋮ → Resources → Add** :
   `/local/ar-duty-cycler-card.js` as a **JavaScript Module**.
3. Add the card (point it at the master switch — it auto-discovers the rest):

```yaml
type: custom:ar-duty-cycler-card
entity: switch.electric_blanket_cycle
# name: Electric Blanket   # optional override
```

---

## Notes

- **Durations** accept half-minute steps (min `0.5`) so you can test with short
  cycles before committing to 10/10.
- **Overnight windows** are supported (e.g. `22:00 → 06:00`).
- A reboot mid-window resumes cycling, starting a fresh phase from the start phase.
- The master switch carries a `cycler_entities` attribute mapping every related
  entity_id — that's what the card uses for auto-discovery.

ARSmartHome · marsh4200
