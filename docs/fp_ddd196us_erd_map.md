# Fisher & Paykel Dual DishDrawer (DDD196US) — ERD Map

Reverse-engineering notes for the F&P dual-drawer dishwasher, built from SmartHQ debug dumps
(`custom_components.ge_home` + `gehomesdk` at DEBUG). Purpose: record which ERDs the appliance
reports, what they mean, and how far the current `gehomesdk`/`ha_gehome` decoding goes — so future
entity/converter work doesn't have to re-derive it from log diffs.

## Appliance identity

| Field | Value |
|---|---|
| Model (`0x0001`) | `DDD196US` |
| Serial (`0x0002`) | `RIV591205` |
| Appliance type (`0x0008`) | `ErdApplianceType.DUAL_DISH_WASHER` (`0x20`) → `DualDishwasherApi` |
| Brand (`0x0099`) | `ErdBrand.FISHER_PAYKEL` (`0x04`) — auto-detected, no model-prefix mapping needed |
| Sound level (`0x000A`) | `ErdSoundLevel.HIGH` |
| WiFi module SW (`0x0100`) | `0.5.15.162` |

Upper-drawer ERDs are *usually* the lower/shared code **+ 0x0200** (e.g. lower `0x3008` → upper `0x3208`,
lower `0xD003` → upper `0xD203`). This holds for most drawer-specific codes — **but not the wash-modifier
register**, which is asymmetric: lower `0x3086`, upper `0x3222` (confirmed 07-23). Don't assume `+0x0200`
for a code you haven't actually observed on both tubs.

## Decoding status legend

- **✅ Decoded** — `gehomesdk` has a converter; value is a rich type. Wired to an HA entity.
- **🟡 Decoded, not exposed** — SDK decodes it, but `DualDishwasherApi` didn't declare an entity
  (now being added for the lower drawer; upper needs SDK converters).
- **🔍 Raw only** — SDK returns raw bytes; meaning inferred from behaviour. No converter yet.
- **❓ Unknown** — reported by the device, meaning not yet determined.

## Lower / shared drawer ERDs

| ERD | Name | Status | Observed | Notes |
|---|---|---|---|---|
| `0x3003` | `DISHWASHER_REMINDERS` | ✅ | `A2` → `add_rinse_aid=True` | 3 property sensors (add_rinse_aid / clean_filter / sanitized) |
| `0x3007` | `DISHWASHER_USER_SETTING` | ✅ | `000004` → cycle_mode=NORMAL | Packed bitfield, **encodable** (see Control) |
| `0x3008` | `DISHWASHER_ERROR` | 🟡→✅ | `0000` → id=0, active=False | Added to dual (lower) |
| `0x3009` | `DISHWASHER_CYCLE_COUNTS` | 🟡→✅ | `0000000C0000` → completed=12 | Added to dual (lower) |
| `0x300C` | `DISHWASHER_UNKNOWN_300C` | ❓ | `0400` (stable so far) | 2 bytes, unchanged across all captures |
| `0x300E` | `DISHWASHER_CYCLE_STATE` | ✅ | `11`=NA idle; `03`=MAIN_WASH running | See cycle-state values below |
| `0x300F` | `DISHWASHER_UNKNOWN_300F` | ❓🔍 | `…62…` (07-18/20) → all-zero (07-21) | 12 bytes; **byte 6 is dynamic** (`0x62`=98, later `00`). Tracks lower `0x320F` identically. Candidate: a temperature/sensor reading, non-zero only mid-heat |
| `0x3037` | `DISHWASHER_DOOR_STATUS` | ✅ | `00`=OPEN / `01`=CLOSED | |
| `0x3086` | `DISHWASHER_UNKNOWN_3086` | ✅🔍 | `00`/`40`/`02`/`04` while idle | **CONFIRMED: lower-drawer wash-modifier register** (Extra Dry=`40` / Quick=`02` / Sanitize=`04`). Same encoding as upper `0x3222`. The earlier "UI-activity indicator" guess was **wrong** — the `00→40→02→00` flicker on 07-21 was the user cycling modifiers |
| `0xD003` | `DISHWASHER_IS_CLEAN` | 🟡→✅ | pulses `01` then `00` at completion | **Transient — see caveat.** Added to dual (lower) |
| `0xD004` | `DISHWASHER_TIME_REMAINING` | ✅ | `0000` → 0:00:00 (idle) | |

## Upper drawer ERDs

| ERD | Name | Status | Observed | Notes |
|---|---|---|---|---|
| `0x3203` | `DISHWASHER_UPPER_REMINDERS` | ✅ | `A2` | |
| `0x3207` | `DISHWASHER_UPPER_USER_SETTING` | ✅ | `00000E`→idle, `000404`→running | See cycle-mode note |
| `0x3208` | `DISHWASHER_UPPER_UNKNOWN_3208` | 🔍 | `0000` | **Inferred: upper error** (mirrors lower `0x3008`, same shape) |
| `0x3209` | `DISHWASHER_UPPER_UNKNOWN_3209` | ✅🔍 | `…10`→16, then `…11`→17 | **CONFIRMED: upper cycle counts.** Ticked 16→17 across a completed cycle (07-20→07-21), proving the +0x0200 mapping. SDK still lacks a converter |
| `0x320E` | `DISHWASHER_UPPER_CYCLE_STATE` | ✅ | `11`=NA → `03`=MAIN_WASH | Tracked a live cycle |
| `0x320F` | `DISHWASHER_UPPER_UNKNOWN_320F` | ❓🔍 | `…62…` → all-zero | Dynamic byte 6, identical to lower `0x300F` |
| `0x3222` | `DISHWASHER_UPPER_UNKNOWN_3222` | ✅🔍 | `00`/`40`/`02`/`04`, cycling while **idle** | **CONFIRMED: wash-modifier register** (Extra Dry / Quick / Sanitize — see mapping below). Earlier "phase indicator" guess was **wrong**: it cycles while `CYCLE_STATE`=NA. SDK has no converter |
| `0x3237` | `DISHWASHER_UPPER_DOOR_STATUS` | ✅ | `01`=CLOSED | |
| `0xD203` | *(unnamed in SDK)* | 🔍 | `00` → 0:00 / False | **Inferred: upper is_clean** (mirrors lower `0xD003`). Keyed uppercase `'0xD203'` in `known_properties` |
| `0xD204` | `DISHWASHER_UPPER_TIME_REMAINING` | ✅ | `000F`=15min idle; `0059`=1:29 → `0058`=1:28 running | Ticks down during cycle |

## Observed value enumerations

**Cycle state** (`0x300E` / `0x320E`, `ErdCycleState`) — observed:
- `0x11` = `NA` (idle / no cycle)
- `0x03` = `MAIN_WASH`
- `0x04` = `DRYING` (watched count down 9→0 min, then → NA at completion)
- (PRE_WASH, RINSE, SENSING, etc. exist in the SDK enum but weren't captured)

**Door status** (`0x3037` / `0x3237`, `ErdDishwasherDoorStatus`): `0x00` = OPEN, `0x01` = CLOSED.

**Cycle counts** (`0x3009` / `0x3209`, `ErdCycleCount`, 6 bytes): the SDK decodes started/completed/reset,
but F&P appears to populate **only the `completed` field** (`started` and `reset` read 0 in every
capture). The counter sits at byte index 3 (lower has reached 13, upper 17). **Trigger still unknown:**
in the 07-21 11:39 log a lower cycle finished (DRYING → NA, time → 0:00) and the counter did **not**
change — it was already 13 before the completion and stayed 13 after. So the +1 seen across earlier
logs (12→13, 16→17) does **not** fire at the DRYING→NA moment. It may increment at cycle *start*, or on
some other event. Do not assume "completed count = number of finished cycles" yet.

**`is_clean` is a momentary pulse, not a level** (⚠️ important for automations): at the 07-21 11:39
completion, `0xD003` went `True` at `11:38:41.007` and back to `False` within the same second — while
the door was still closed (it opened 30 s later). A 30-second poll will almost always miss it. To detect
"cycle finished" reliably, watch the **`CYCLE_STATE` DRYING→NA transition** (or `TIME_REMAINING`→0),
not the `is_clean` sensor.

**`TIME_REMAINING` doubles as a program-duration preview:** while idle (`CYCLE_STATE = NA`), scrolling
programs on the panel made `0xD004` show each program's estimated length — observed `1:30`, `2:00`,
`2:05`, `2:30`, `3:05` — before any cycle started. So the value is meaningful even when not running.

**User setting bitfield** (`0x3007` / `0x3207`, `ErdUserSetting`, 3 bytes big-endian). Observed
raw → decoded (from live panel-scrolling on the lower drawer):

| raw | cycle_mode | dry_option | notes |
|---|---|---|---|
| `000004` | NORMAL (2) | OFF (0) | |
| `00000C` | RINSE (6) | OFF (0) | |
| `000010` | **AUTO (0)** | OFF (0) | |
| `000404` | NORMAL (2) | POWER_DRY (1) | |
| `000C04` | NORMAL (2) | **FP_UNKNOWN_3 (3)** | real dry option the SDK enum doesn't name |
| `00000E` | FP_UNKNOWN (7) | OFF (0) | **idle placeholder**, not a real cycle |

- `cycle_mode` ≈ bits 1–3 (`(value>>1)&0x7`): AUTO=0, NORMAL=2, RINSE=6, idle=7.
- `dry_option` = bits 10–11 (`0xC00` mask): OFF=0 (`…000`), POWER_DRY=1 (`…400`), FP_UNKNOWN_3=3 (`…C00`).
  **`FP_UNKNOWN_3` is a genuine gap** — a real dry setting on this machine that `UserDryOptionSetting`
  doesn't name (contrast with cycle `FP_UNKNOWN`, which is just the idle state).
- `delay_hours` = bits 16–19 (high byte). **Confirmed live 07-23:** setting a 1-hour delay on the lower
  drawer pushed `0x3007` = `010004` (SDK decoded `delay_hours=1`) with `0xD004` previewing `1:00`; clearing
  it returned to `000004`. Works with the drawer open — it's a setting, not a cycle start.
- Other packed fields per SDK, not yet ground-truthed on F&P: mute, demo_mode, lock_control, sabbath,
  presoak, bottle_jet, wash_temp, rinse_aid, wash_zone, wifi_enabled.

> ⚠️ **The GE SDK field *names* are wrong for F&P — trust the bits, not the labels.**
> Ground-truth (user-confirmed): the 07-21 lower run was a **"Medium" wash with the "Quick" modifier**,
> and the machine reported `000404` the entire time. Under GE's layout that decodes as
> `cycle_mode=NORMAL(2)` + `dry_option=POWER_DRY(1)`. So on this appliance:
> - bits 1–3 value **2** = panel **"Medium"** (GE calls it NORMAL)
> - bits 10–11 value **1** = panel **"Quick"** modifier (GE calls it dry_option POWER_DRY)
>
> The bit *positions* are shared with GE, but the *semantics are rebranded*. Consequence: a control or
> display entity built on the GE `ErdUserSettingConverter` decode will show **incorrect labels** for
> F&P. Proper support needs an **F&P-specific user-setting interpretation** (enum values re-labelled to
> F&P's program/modifier names), not just a rename of `FP_UNKNOWN_3`. Every raw→label mapping below must
> be confirmed against the physical panel — do not infer from the GE decode.

**Confirmed F&P panel mappings.** The wash *program* is identified by the **low byte** of the
`0x3007`/`0x3207` value (GE's 3-bit `cycle_mode` slice is too narrow — see below). Modifiers live in the
higher bits.

*Wash programs* (user-confirmed 07-22, order-aligned; anchored by Medium=`04` which was confirmed
independently):

| F&P panel label | low byte | GE `cycle_mode` decode (WRONG) |
|---|---|---|
| **Eco** | `0C` | RINSE (6) |
| **Fast** | `12` | INTENSE (1) |
| **Delicate** | `10` | AUTO (0) |
| **Rinse** | `0E` | FP_UNKNOWN (7) |
| **Heavy** | `02` | INTENSE (1) |
| **Medium** | `04` | NORMAL (2) |

*Modifiers* — **CONFIRMED live 2026-07-23** via a labeled sweep on the **upper** drawer (idle, program
held at Medium=`04`; modifiers cycled Extra Dry → Quick → Sanitize twice, identical both passes). The
selected modifier is reported in the **separate `0x3222` register** (upper) — *not* in the `0x3207`
user-setting bits — while idle. `0xD204` time-remaining moves in lockstep and corroborates each:

| F&P modifier | modifier register | `0xD204`/`0xD004` (from Medium base 150 min) |
|---|---|---|
| None | `0x00` | 150 (2:30) |
| **Extra Dry** | `0x40` | 185 (3:05, +35) |
| **Quick** | `0x02` | 90 (1:30) |
| **Sanitize** | `0x04` | 200 (3:20) |

- **⚠️ The modifier register is ASYMMETRIC between tubs** — it does *not* follow the usual `+0x0200`
  rule. **Upper = `0x3222`, lower = `0x3086`** (both confirmed live 07-23 with the identical value
  encoding above). There is no `0x3022` ERD. Both are wired to `GeDishwasherModifierSensor` in
  `dual_dishwasher.py`.
- Distinct bits (`0x40`/`0x02`/`0x04`) — the appliance *could* combine them, though the panel cycles
  them exclusively. (Lower `Quick`=`0x02` seen in the 07-21 flicker, not re-captured in the 07-23 pass
  which went Extra Dry → Sanitize → off.)
- ⚠️ **Reconciliation with the 07-21 lower-drawer capture:** that run (a *running* cycle) showed "Quick"
  committed into `0x3007` **bits 10–11** (`…400`, GE `dry_option`). Here (idle) Quick is `0x3222 = 0x02`.
  **✅ CONFIRMED 07-23:** `0x3086`/`0x3222` is the **pre-start selection**; it **commits (re-encoded) into
  the user-setting bits on Start**. Live capture: idle Quick `0x3086 = 0x02`, then on remote start
  `0x3007` bits 10–11 → `1` (`0x400`, GE `dry_option=POWER_DRY`) with `CYCLE_STATE`→MAIN_WASH. Note it's a
  **re-encode, not a bit-copy** (`0x02` → bit-field value `1`). Extra Dry/Sanitize commit mapping (into
  bits 10–11 vs. 12–13 `wash_temp`) still to be captured individually.

- **GE's `cycle_mode` (bits 1–3) cannot distinguish F&P programs:** Fast (`0x12`) and Heavy (`0x02`)
  both decode to GE `cycle_mode = 1`, differing only in **bit 4** which GE ignores. Use the **whole low
  byte** as the program key. (Re-confirmed live 07-23: Fast=`12`, Delicate=`10`, Heavy=`02`, Medium=`04`,
  Eco=`0C` all observed on `0x3207`.)
- **No "idle" cycle value:** a resting drawer holds its **last-selected program** (earlier `0E`/`0C`
  "idle" readings were just Rinse/Eco held). The prior "cycle 7 = idle placeholder" note was **wrong** —
  `0E` = **Rinse**.

## Door / open detection

- **Opening a drawer is signalled in real time** via a dedicated ERD per drawer:
  `DISHWASHER_DOOR_STATUS 0x3037` (lower) / `DISHWASHER_UPPER_DOOR_STATUS 0x3237` (upper).
  Values: `0x00` = **OPEN**, `0x01` = **CLOSED**.
- **It's a websocket push, not a poll artifact.** In the 07-21 cycle log the lower door opened and the
  ERD fired at `11:39:11.012` — off the `:00`/`:30` poll cadence — i.e. sent the instant the drawer
  opened. Confirmed again 07-22 (upper OPEN pushed at `10:16:16`).
- **It's a level, not a pulse** (unlike `is_clean`): reads OPEN and stays OPEN until closed. Reliable for
  automations like "notify if a drawer is left open." Already exposed as HA binary sensors
  (`..._lower_door_status` / `..._upper_door_status`).
- The door event is **isolated** — opening (after a finished cycle) did not by itself change `is_clean`
  or cycle state.
- ⚠️ **Not yet captured: a mid-cycle door open.** Every observed open was *after* a cycle ended. F&P
  drawers normally pause when opened during a run; whether that also changes `CYCLE_STATE` is unconfirmed
  (capture a pause-by-open to close this gap).
- **`0x3086` RESOLVED:** the 07-21 `00→40→02→00` flicker was **not** UI activity — it was the user cycling
  **wash modifiers**. `0x3086` is the **lower-drawer modifier register** (Extra Dry=`40`/Quick=`02`/
  Sanitize=`04`), confirmed by the labeled 07-23 sweep. See the modifier mapping above.

## Remote control (start / pause / cancel)

- Command ERDs `DISHWASHER_REMOTE_START_COMMAND 0x3204` (lower) / `0x3604` (upper) drive the existing
  per-drawer Start/Pause/Cancel buttons in `DualDishwasherApi` (via `GeDishwasherCommandButton`, which
  writes an `ErdRemoteCommand`).
- **Both drawers reported `wifi_enabled = DISABLE`** in every capture. Per the code comment in
  `dual_dishwasher.py`, remote is armed by a **physical button per drawer** and cleared when the drawer
  is opened. So the HA buttons exist but the machine ignores them until each drawer is armed.
- **The CANCEL buttons were pressed** (both drawers, 2026-07-20 17:14 — recorded as the button
  entities' last-pressed state). Start/Pause were never pressed (`unknown`). So a live cancel *write*
  was issued, but with `wifi_enabled = DISABLE` at the time and no state capture around the press, the
  **outcome is inconclusive** — we can't tell from the logs whether the machine acted on it.
- **✅ CONFIRMED 07-23: remote start is honored when the drawer is armed.** Sequence captured live on
  the lower drawer: armed via the panel (→ `wifi_enabled = ENABLE`, see below), door closed, then a
  **SmartHQ-app remote start** drove `CYCLE_STATE 0x300e`: `NA (0x11)` → `MAIN_WASH (0x03)`. So the
  appliance *does* act on a remote command once armed. (The HA integration's own `0x3204` write path
  wasn't exercised in this test — the app was used — but the appliance-side behavior is now proven.)
- **Arm state is observable:** arming sets **`wifi_enabled` = bit 7 (`0x80`) of `0x3007`/`0x3207`**
  (raw went to `…84` = Medium `04` + armed `80`). Opening the drawer clears it. Watch this bit to know
  whether a remote command will be accepted.
- **Bits 20–21 are NOT a running flag** (correction, 07-23). They read `0b11` (`0x30xxxx`, GE
  `wash_zone = BOTH_ALT`) on the lower drawer **even at idle** (`CYCLE_STATE = NA`) — the live baseline
  showed `0x3007 = 300084` while idle. So `0x30xxxx` is just this drawer's persistent `wash_zone`, not a
  running indicator. **Use `CYCLE_STATE` `0x300e`/`0x320e` (NA ↔ MAIN_WASH) as the running signal**, never
  these bits. (The upper drawer read `wash_zone = 0` at idle — the field genuinely differs per tub.)

## Program / modifier control — feasibility

- The appliance does **not** report the dedicated cycle-selection ERDs the SDK knows about
  (`0x321b` CYCLE, `0x321c` TEMPERATURE, `0x321d` DRYING, `0x321e` WASH_ZONE, `0x321f` STEAM,
  `0x3220` BOTTLE_JETS) — nor `DISHWASHER_CYCLE_NAME 0x301c` / `DISHWASHER_OPERATING_MODE 0x3001`.
  Verified absent (zero hits across dumps).
- Program/modifier state lives **inside the `0x3007`/`0x3207` user-setting bitfield** instead
  (cycle_mode, wash_temp, dry_option, presoak, bottle_jet, wash_zone).
- `ErdUserSettingConverter` extends `ErdReadWriteConverter` and implements `erd_encode()` — **but do
  NOT use it to write F&P settings.** Its `erd_encode()` rebuilds the word from only the GE-known
  fields (dropping the F&P program low-byte beyond bit 3, `wash_zone`, etc.) and calls
  `erd_encode_int()` with the **default 2-byte length**, which overflows the moment `delay_hours`/
  `wash_zone` bits are set. Writing through it corrupts the word. **Write raw hex instead** (read the
  raw value, flip only the target bits, push the raw string via `appliance.client.async_set_erd_value`).
- **✅ WRITE CONTROL PROVED 2026-07-23.** A raw read-modify-write to `0x3007` on the lower drawer
  (program Medium `300004` → Eco `30000c`, only bits 1–4 changed) was **accepted, echoed, and held**:
  the appliance pushed `0x3007 = 30000c` back and kept it (no bounce to `300004`), and — proving it
  *acted* on the change rather than just storing it — `0xD004` time-remaining **recomputed to `0x78` =
  120 min** (the Eco cycle length). The RMW preserved every co-located bit (`wash_zone`, arm, dry,
  delay). This was done on an **idle, empty, closed** drawer. (In the same response the SDK decoded the
  new word as `cycle_mode = RINSE`, re-confirming the GE-label problem.)
- **Gaps before a control entity is viable:**
  1. ~~No HA entity currently writes user settings — all `GeErdPropertySensor` (read-only).~~ **✅ DONE**:
     `GeDishwasherProgramSelect` (`lower_program`/`upper_program`) and `GeDishwasherModifierSelect`
     (`lower_wash_modifier`/`upper_wash_modifier`) — both per drawer, both raw-RMW writes. Wired in
     `dual_dishwasher.py`, **gated on brand = Fisher & Paykel** (`_is_fisher_paykel()`, ERD `0x0099`):
     the F&P low-byte program map and modifier registers are only ground-truthed on F&P hardware, and
     the selectors *write*, so a non-F&P dual unit keeps the generic read-only entities and skips this
     block. (The old read-only `GeDishwasherModifierSensor` was replaced by the select, which subsumes it.)
  2. ~~Modifier write isn't reliable — commit-on-Start path only partially mapped.~~ **✅ RESOLVED**:
     we don't need the `0x3007` commit mapping to *set* a modifier — writing the modifier **register**
     directly (`0x3086`/`0x3222`) works. **Verified live 2026-07-23**: cloud writes of Quick (`0x02`) and
     Sanitize (`0x04`) to `0x3086` both **held** and **lit up the physical panel** (a real selection, not
     a stored byte). The appliance handles committing it into `0x3007` on Start itself. (Selecting a
     *program* at the panel clears the modifier — observed — which is normal and reflected on the next push.)
  3. Writing a packed struct risks clobbering co-located fields (lock_control, sabbath, demo_mode) —
     any write must read-modify-write the current value. **✅ Handled**: the proven write path is raw
     RMW on the low byte, mask `0x1E`, which leaves all other bits intact.
  4. ~~Whether the appliance accepts the write is unverified.~~ **✅ RESOLVED — it does (see above).**

## Open items / next captures

Priority order reflects that **GE decode labels are unreliable for F&P** (see the ⚠️ note above): a
labeled panel sweep is now the highest-value capture, because raw bits are meaningless without the panel
label that produced them.

### 🥇 1. Labeled settings sweep (lower drawer, idle, at the panel)

Change one thing at a time; for each, **record the panel label** — I'll read the `0x3007` raw. The
machine pushes an update on every change, so one short capture session covers the whole list.

**A. Wash programs** — select each; note its panel name:
- [ ] Medium ✅ (confirmed: cycle field value 2)
- [ ] Heavy
- [ ] Eco
- [ ] Delicate / Fragile
- [ ] Fast / Quick-wash (if a standalone *program*, distinct from the Quick *modifier*)
- [ ] Rinse / Rinse-only
- [ ] Auto (if present)
- [ ] any other program on the panel

**B. Modifiers** — ✅ **DONE 07-23** (upper drawer, idle). They live in the **`0x3222` register**, not the
`0x3007`/`0x3207` bits, when idle:
- [x] Quick → `0x3222 = 0x02`
- [x] Sanitize → `0x3222 = 0x04`
- [x] Extra Dry → `0x3222 = 0x40`
- [x] **Commit-on-Start proved 07-23**: the selection register commits (re-encoded) into `0x3007` bits
      10–11 on Start — Quick `0x3086=0x02` → bits 10–11=`1`. Extra Dry/Sanitize commit targets TBD.
- [ ] Rinse aid boost, Half load, Delay start, Child lock, Mute — whatever the panel offers

**C. Isolation check** (proves the Quick bits cleanly):
- [ ] Medium with **no** modifiers → record raw
- [ ] Medium **+ Quick only** → record raw; the delta = the Quick bits exactly

> **07-23 start attempt (inconclusive):** physical Start/Cancel were pressed on the lower drawer but the
> **drawer was open** the whole time, so no cycle could begin — `CYCLE_STATE` stayed `NA` and nothing
> moved. A valid Start test must be done with the **drawer closed**. `delay_hours` was captured here (see
> bitfield note); the Start→`CYCLE_STATE` transition and the modifier commit-on-Start path remain open.

### 🥈 2. Live remote test

- [x] **Appliance-honors-remote-start PROVED 07-23** via the SmartHQ app (armed → `NA`→`MAIN_WASH`).
      Still worth doing: exercise the **HA integration's own** `0x3204` write (its Start button) to prove
      *that* path end-to-end, since the 07-23 test used the app, not HA.

### 🥉 3. One full cycle, start → finish (fresh load)

Resolves several at once:
- [ ] Missing **cycle states** (PRE_WASH, SENSING, RINSE, …) with their numeric codes
- [ ] **Cycle-count trigger** — does `0x3009`/`0x3209` tick at *start*? (it did **not** at completion)
- [ ] **`is_clean`** — is the True pulse always ~1 s, or does it sometimes latch until the door opens?
- [ ] **Temperature candidate** — does `0x300F`/`0x320F` byte 6 rise during heat/wash and fall otherwise?

### 4. Remaining unknown ERDs (lower priority)

- [x] `0x3086` — **RESOLVED**: it's the *lower-drawer* wash-modifier register (Extra Dry=`40`/Quick=`02`/
      Sanitize=`04`), not UI noise. Wired to `GeDishwasherModifierSensor`.
- [ ] `0x300C` (`0400`) — has it *ever* changed? If constant, likely a config/capability value, not state
- [x] `0x3222` — **RESOLVED**: it's the wash-modifier register (Extra Dry=`40`, Quick=`02`, Sanitize=`04`),
      not a phase indicator. Cycles while idle. See modifier mapping above.

## Capture provenance

- `home-assistant_2026-07-19T04-32-38.379Z.log` — first `ha_gehome` run; both drawers idle. Baseline.
- `home-assistant_2026-07-20T06-26-55.371Z.log` — upper drawer running a Normal cycle
  (`MAIN_WASH`, time ticking `1:29→1:28`, dry_option=POWER_DRY). Source of the cycle-mode / running-state
  deltas above.
- `home-assistant_2026-07-21T17-23-26.479Z.log` — lower drawer running (MAIN_WASH, 1:28), upper idle
  set to RINSE. Upper cycle count now 17 (was 16) — **confirms cycle-counts mapping**. CANCEL buttons
  show 07-20 presses. `0x3086`=`40`, `0x300F`/`0x320F` all-zero — established those bytes are dynamic.
- `home-assistant_2026-07-21T18-39-41.922Z.log` — **richest capture.** Lower drawer's DRYING phase
  counted down 9→0 min to completion (DRYING→NA). Source of: `0x04`=DRYING, the `is_clean` transient
  pulse, the observation that the cycle counter did *not* tick at completion, the expanded
  cycle_mode/dry_option map (AUTO, FP_UNKNOWN_3) from live panel-scrolling, and TIME_REMAINING as a
  program-duration preview.
- All three 07-20/07-21 logs still lack the added lower/upper status entities → the code change remained
  undeployed as of the latest capture.
- **Live watcher session 2026-07-23 13:21–13:24** (`scratchpad/dishwasher_watch.py`, direct `gehomesdk`
  websocket, upper drawer). First *labeled* sweep. Confirmed programs live in `0x3207` low byte
  (Fast=`12`, Delicate=`10`, Heavy=`02`, Medium=`04`; Eco=`0C` baseline) with `0x3222` unmoved, then with
  the program held at Medium confirmed the modifier register `0x3222` = Extra Dry(`40`)/Quick(`02`)/
  Sanitize(`04`), each corroborated by `0xD204`. Disproved the `0x3222` "phase indicator" theory.
  Then repeated on the **lower** drawer: programs again in `0x3007` low byte (Fast/Delicate/Rinse/Medium),
  and the modifier surfaced in **`0x3086`** (Extra Dry=`40`, Sanitize=`04`) — revealing the modifier
  register is **asymmetric** (lower `0x3086` ≠ upper−0x200) and that the old `0x3086` "UI-activity" guess
  was really modifier cycling. Killed the `0x3022` prediction (no such ERD). Same session, ~13:39–13:41:
  captured `delay_hours` (`0x3007`=`010004`), then armed the lower drawer (Medium+Quick) and did a
  **SmartHQ-app remote start** → `CYCLE_STATE`→`MAIN_WASH`, proving remote start is honored, that arming =
  `wifi_enabled` bit 7 (`…84`), and that the modifier commits (re-encoded) into `0x3007` bits 10–11 on Start.
- **Live write-test session 2026-07-23 14:00–14:10** (`scratchpad/dishwasher_watch.py` +
  `scratchpad/dishwasher_set.py`, lower drawer). Re-observed the modifier register `0x3086`
  (Quick=`02`/Extra Dry=`40`/Sanitize=`04`, persisting through a running cycle) and the program low byte
  (Fast=`12`/Heavy=`02`/Medium=`04`). Established **bits 20–21 = `wash_zone`, set at idle** (not a running
  flag). **Then proved write control**: a raw RMW `dishwasher_set.py` wrote program Medium→Eco
  (`300004`→`30000c`) to `0x3007`; the appliance echoed and held `30000c` and recomputed `0xD004` to
  120 min. Note: Extra Dry/Sanitize commit-into-`0x3007` remained ambiguous in this fast manual sweep
  (both starts landed on `dry_option=1`), so the modifier→setting-word mapping is still not pinned —
  the modifier itself lives durably in `0x3086`, which is the register a modifier control should target.
- **Live modifier-write test 2026-07-23 14:21–14:24** (`scratchpad/dishwasher_modifier_set.py`, lower
  drawer). Raw writes to the modifier register `0x3086` — Quick (`0x00`→`0x02`) then Sanitize
  (`0x00`→`0x04`) — each **held** the full 40 s watch window AND **lit the corresponding modifier on the
  physical panel** (user-confirmed). Proves modifier write control end to end: the appliance accepts a
  cloud-written modifier as a real selection. Between the two writes the user switched the program to
  Medium at the panel, which cleared the modifier to None (normal — a program change resets modifiers).
  → `GeDishwasherModifierSelect` built on this (replaces the read-only modifier sensor).
