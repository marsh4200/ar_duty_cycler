/*! AR Duty Cycler Card  v1.0.0  -  ARSmartHome
 *
 *  Point it at the cycler's master switch; it auto-discovers the rest.
 *
 *    type: custom:ar-duty-cycler-card
 *    entity: switch.electric_blanket_cycle
 */

const STATUS_LABEL = {
  idle: "Idle",
  waiting: "Waiting for window",
  running_on: "Running — ON",
  running_off: "Running — OFF",
};
const STATUS_COLOR = {
  idle: "var(--disabled-text-color, #9e9e9e)",
  waiting: "var(--warning-color, #ffa600)",
  running_on: "var(--success-color, #43a047)",
  running_off: "var(--info-color, #039be5)",
};

class ARDutyCyclerCard extends HTMLElement {
  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("ar-duty-cycler-card: 'entity' (the cycler switch) is required");
    }
    this._config = config;
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) this._build();
    this._update();
  }

  getCardSize() {
    return 5;
  }

  // ---- discovery -------------------------------------------------------- //
  get _switch() {
    return this._hass && this._hass.states[this._config.entity];
  }
  get _map() {
    const s = this._switch;
    return (s && s.attributes.cycler_entities) || {};
  }
  _state(role) {
    const id = this._map[role];
    return id ? this._hass.states[id] : undefined;
  }

  // ---- service helpers -------------------------------------------------- //
  _call(domain, service, data) {
    this._hass.callService(domain, service, data);
  }
  _setNumber(role, value) {
    const id = this._map[role];
    if (id) this._call("number", "set_value", { entity_id: id, value });
  }
  _bumpNumber(role, delta) {
    const st = this._state(role);
    if (!st) return;
    const step = Number(st.attributes.step || 0.5);
    const min = Number(st.attributes.min || 0.5);
    const max = Number(st.attributes.max || 1440);
    let v = Number(st.state) + delta * step;
    v = Math.min(max, Math.max(min, Math.round(v / step) * step));
    this._setNumber(role, v);
  }
  _setTime(role, value) {
    const id = this._map[role];
    if (id && value) {
      const t = value.length === 5 ? `${value}:00` : value;
      this._call("time", "set_value", { entity_id: id, time: t });
    }
  }
  _setSelect(role, option) {
    const id = this._map[role];
    if (id) this._call("select", "select_option", { entity_id: id, option });
  }

  // ---- DOM -------------------------------------------------------------- //
  _build() {
    this.innerHTML = `
      <ha-card>
        <style>
          .wrap { padding: 16px; }
          .head { display:flex; align-items:center; justify-content:space-between; gap:12px; }
          .title { font-size:1.15rem; font-weight:600; color:var(--primary-text-color); }
          .pill { font-size:.78rem; font-weight:600; padding:3px 10px; border-radius:14px;
                  color:#fff; white-space:nowrap; }
          .target { margin-top:4px; font-size:.85rem; color:var(--secondary-text-color); }
          .master { display:flex; align-items:center; justify-content:space-between;
                    margin:14px 0; padding:10px 12px; border-radius:12px;
                    background:var(--secondary-background-color); }
          .master .lbl { font-weight:500; color:var(--primary-text-color); }
          .grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
          .field { background:var(--secondary-background-color); border-radius:12px; padding:10px 12px; }
          .field .k { font-size:.72rem; text-transform:uppercase; letter-spacing:.04em;
                      color:var(--secondary-text-color); margin-bottom:6px; }
          .stepper { display:flex; align-items:center; gap:8px; }
          .stepper input { width:100%; text-align:center; font-size:1rem; padding:6px 4px;
                           border:1px solid var(--divider-color); border-radius:8px;
                           background:var(--card-background-color); color:var(--primary-text-color); }
          .btn { cursor:pointer; border:none; border-radius:8px; width:34px; height:34px;
                 font-size:1.2rem; line-height:1; background:var(--primary-color); color:#fff; }
          .btn:active { filter:brightness(.9); }
          .unit { font-size:.72rem; color:var(--secondary-text-color); margin-top:4px; text-align:center; }
          input[type=time], select { width:100%; padding:7px 6px; border-radius:8px;
                          border:1px solid var(--divider-color); background:var(--card-background-color);
                          color:var(--primary-text-color); font-size:.95rem; box-sizing:border-box; }
          .full { grid-column:1 / -1; }
          ha-switch { --mdc-theme-secondary: var(--primary-color); }
        </style>
        <div class="wrap">
          <div class="head">
            <div>
              <div class="title" id="title"></div>
              <div class="target" id="target"></div>
            </div>
            <div class="pill" id="pill"></div>
          </div>

          <div class="master">
            <span class="lbl">Cycle</span>
            <ha-switch id="master"></ha-switch>
          </div>

          <div class="grid">
            <div class="field">
              <div class="k">ON duration</div>
              <div class="stepper">
                <button class="btn" id="onMinus">−</button>
                <input type="number" id="onVal" step="0.5" min="0.5" />
                <button class="btn" id="onPlus">+</button>
              </div>
              <div class="unit">minutes</div>
            </div>

            <div class="field">
              <div class="k">OFF duration</div>
              <div class="stepper">
                <button class="btn" id="offMinus">−</button>
                <input type="number" id="offVal" step="0.5" min="0.5" />
                <button class="btn" id="offPlus">+</button>
              </div>
              <div class="unit">minutes</div>
            </div>

            <div class="field">
              <div class="k">Window start</div>
              <input type="time" id="winStart" />
            </div>
            <div class="field">
              <div class="k">Window end</div>
              <input type="time" id="winEnd" />
            </div>

            <div class="field">
              <div class="k">When window closes</div>
              <select id="park">
                <option value="on">Force ON</option>
                <option value="off">Force OFF</option>
              </select>
            </div>
            <div class="field">
              <div class="k">Start phase</div>
              <select id="startPhase">
                <option value="on">Start ON</option>
                <option value="off">Start OFF</option>
              </select>
            </div>
          </div>
        </div>
      </ha-card>`;

    const $ = (id) => this.querySelector("#" + id);

    $("master").addEventListener("change", (e) => {
      this._call("switch", e.target.checked ? "turn_on" : "turn_off", {
        entity_id: this._config.entity,
      });
    });

    $("onMinus").addEventListener("click", () => this._bumpNumber("on_duration", -1));
    $("onPlus").addEventListener("click", () => this._bumpNumber("on_duration", +1));
    $("offMinus").addEventListener("click", () => this._bumpNumber("off_duration", -1));
    $("offPlus").addEventListener("click", () => this._bumpNumber("off_duration", +1));
    $("onVal").addEventListener("change", (e) => this._setNumber("on_duration", Number(e.target.value)));
    $("offVal").addEventListener("change", (e) => this._setNumber("off_duration", Number(e.target.value)));

    $("winStart").addEventListener("change", (e) => this._setTime("window_start", e.target.value));
    $("winEnd").addEventListener("change", (e) => this._setTime("window_end", e.target.value));

    $("park").addEventListener("change", (e) => this._setSelect("park_state", e.target.value));
    $("startPhase").addEventListener("change", (e) => this._setSelect("start_phase", e.target.value));

    this._built = true;
  }

  _update() {
    const sw = this._switch;
    if (!sw) return;
    const $ = (id) => this.querySelector("#" + id);
    const active = (el) => el && document.activeElement === el;

    const status = sw.attributes.status || "idle";
    $("title").textContent =
      this._config.name || sw.attributes.friendly_name || "Duty Cycler";
    $("pill").textContent = STATUS_LABEL[status] || status;
    $("pill").style.background = STATUS_COLOR[status] || STATUS_COLOR.idle;

    const tgt = this._state("target");
    if (tgt) {
      $("target").textContent = `${tgt.attributes.friendly_name || tgt.entity_id}: ${
        tgt.state
      }`;
    } else {
      $("target").textContent = "";
    }

    $("master").checked = sw.state === "on";

    const on = this._state("on_duration");
    if (on && !active($("onVal"))) $("onVal").value = on.state;
    const off = this._state("off_duration");
    if (off && !active($("offVal"))) $("offVal").value = off.state;

    const ws = this._state("window_start");
    if (ws && !active($("winStart"))) $("winStart").value = (ws.state || "").slice(0, 5);
    const we = this._state("window_end");
    if (we && !active($("winEnd"))) $("winEnd").value = (we.state || "").slice(0, 5);

    const park = this._state("park_state");
    if (park) $("park").value = park.state;
    const sp = this._state("start_phase");
    if (sp) $("startPhase").value = sp.state;
  }
}

customElements.define("ar-duty-cycler-card", ARDutyCyclerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ar-duty-cycler-card",
  name: "AR Duty Cycler Card",
  description: "Control panel for an AR Duty Cycler instance.",
});

console.info("%c AR-DUTY-CYCLER-CARD %c v1.0.0 ", "background:#0288d1;color:#fff", "color:#0288d1");
