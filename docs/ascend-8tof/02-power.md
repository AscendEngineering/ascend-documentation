# Power & Voltage Ranges

All values below are taken from the KiCad schematic/netlist; regulator outputs are
computed from the feedback dividers with the math shown so you can verify against
the board.

## Power tree

```
                  ┌─ J1 (DF13 2-pin) ──► CR1 (Schottky OR) ─┐
 external DC ─────┤                                          ├──► +5V bus ──► U4 (TPS54360B) ──► +3V3 ──► U2 (TPS62130) ──► +1V8
                  └─ J2 (USB-C VBUS) ─► F1 (500mA) ─► D1 ────┘         │  (buck)                  │  (buck)                  │
                                                                        │                          │                          │
                                                          U1 USBLC6, J7(+5 via D3)     MCU/mux/pull-ups, sensors    sensor IOVDD/CORE, LED PG
```

Three rails: **+5V** (input bus), **+3V3**, **+1V8**. There is *no* separate LDO —
1.8 V is a second switching regulator fed from 3.3 V.

## Input — the `+5V` bus

Two sources are OR-ed onto the `+5V` net through Schottky diodes so either can
power the board:

| Source | Path | Protection |
|--------|------|-----------|
| **J1** (DF13-02P) | J1.1 → **CR1** (B560C, 5 A/60 V Schottky) → +5V | reverse-polarity / OR-ing diode |
| **J2** USB-C VBUS | VBUS → **F1 (500 mA fuse)** → **D1** (SS14 Schottky) → +5V | fuse + OR-ing diode |

- USB-C `CC1/CC2` have **5.1 kΩ Rd pull-downs** (R1/R2) → the port presents as a
  **sink/device** (accepts 5 V default USB power).
- `+5V` also feeds the USBLC6 (U1) VBUS clamp and is exported (via **D3**) to J7
  pin 1.

### ⚠️ Input voltage range — read this

- **U4 is a TPS54360B-Q1, rated 4.5 – 60 V input**, so the buck silicon itself
  tolerates a wide DC input on J1.
- **However, the input net is shared with 5 V-class parts** — the USBLC6 (U1) VBUS
  pin and the USB OR-ing diode D1 sit on the same `+5V` node. The board is designed
  around a **nominal 5 V** input.
- The regulator's **enable/UVLO divider** (R9 = 200 kΩ / R10 = 84.5 kΩ on EN)
  gives **turn-on ≈ 4.7 V, turn-off ≈ 4.0 V** — consistent with 5 V operation.
- **Recommended input: 5.0 V (USB-C) or 5.0–5.5 V on J1.** If you intend to drive
  J1 from a higher bus (e.g. a battery rail), **first confirm the USBLC6 VBUS
  rating and D1 handling** on the shared `+5V` net before doing so. Do not assume
  the 60 V buck rating applies to the whole board.

Input/bulk capacitance on +5V: C3/C6/C7 (10 µF) + C22/C24 (2.2 µF).

## +3V3 rail — U4 TPS54360B-Q1 buck

| Parameter | Value |
|-----------|-------|
| Input | +5V bus |
| Output | **+3.3 V** (computed 3.28 V) |
| Feedback | R13 = 31.6 kΩ (top), R14 = 10.2 kΩ (bottom) |
| Switch node | SW → **L2 = 10 µH** (NRS6045) → +3V3 |
| Catch diode | CR2 (B560C Schottky) |
| Switching freq | ≈ 480–500 kHz (R11 = 162 kΩ on RT/CLK) |
| Output caps | C31/C32 (47 µF), C2/C12 (10 µF), C20 (4.7 µF) + 100 nF decouplers |

**Vout math:** `Vout = 0.8 V × (1 + R13/R14) = 0.8 × (1 + 31.6/10.2) = 0.8 × 4.098
= 3.28 V ≈ 3.3 V.` ✓

**Enable/UVLO:** R9 = 200 kΩ (VIN→EN), R10 = 84.5 kΩ (EN→GND) → turn-on ≈ 4.7 V,
turn-off ≈ 4.0 V (with internal hysteresis current).

Loop compensation on COMP: R12 = 13.0 kΩ + C29 = 6800 pF (series) and C30 = 39 pF.

**What +3V3 powers:** STM32 (IC1) VDD, TCA9548A (U3) VCC, I²C1 pull-ups R4/R5, the
SWD connector (J9 pin 6), and **pin 1 of every sensor connector** (VL53L8CX AVDD).

## +1V8 rail — U2 TPS62130 buck

| Parameter | Value |
|-----------|-------|
| Input | **+3V3** (derived from the 3.3 V rail) |
| Output | **+1.8 V** |
| Switch node | SW → **L1 = 2.2 µH** (NRS4018) → +1V8 |
| Output cap | C8 = 22 µF |
| Enable | EN = +3V3 (always on) |
| Soft-start | C5 = 3.3 nF on SS/TR |
| Preset select | FB/FSW/**DEF tied to GND** — output preset by DEF pin |

> The TPS62130 here uses its **internal feedback with the DEF-pin voltage preset**,
> not an external Vfb = 0.8 V resistor divider (there is no external divider on
> +1V8). VOS pin senses the output directly. That's why you won't find an R-divider
> setting 1.8 V.

**Power-good / LED:** PG (open-drain) = `/1V8_PG`, pulled up by R3 (100 kΩ → +1V8)
and R6 (1 kΩ → +3V3), and drives **LED D2** — so **D2 lit = the 1.8 V rail is
good**.

**What +1V8 powers:** **pin 2 of every sensor connector** (VL53L8CX IOVDD +
CORE_1V8), and via the sub-board it is also the rail the sensor I²C pull-ups
(R1/R2) and mode straps (LPn/SYNC) reference.

## Rail summary

| Rail | Nominal | Source | Tolerance/notes | Loads |
|------|---------|--------|-----------------|-------|
| **+5V** | 5.0 V | J1 or USB-C VBUS (OR-ed via CR1 / D1) | design point 5 V; UVLO ~4.0–4.7 V | U4 buck input, USBLC6, J7 pin1 (via D3) |
| **+3V3** | 3.28 V | U4 TPS54360B buck | 0.8 V ref × 4.098 | STM32, mux, I²C pull-ups, SWD, sensor AVDD |
| **+1V8** | 1.8 V | U2 TPS62130 buck (from +3V3) | DEF-preset, internal FB | sensor IOVDD/CORE, sensor pull-ups & straps |

## Protection & indicators

| Part | Function |
|------|----------|
| F1 (500 mA fuse) | on **USB-C VBUS input only** (not the J1 input) |
| CR1 (B560C) | J1 input reverse-polarity / OR-ing Schottky |
| D1 (SS14) | USB VBUS OR-ing / reverse-block Schottky onto +5V |
| CR2 (B560C) | U4 buck catch/freewheel diode |
| D3 (SS14) | isolates +5V exported to J7 pin 1 (prevents back-feed) |
| U1 (USBLC6-2SC6) | USB D+/D− ESD/TVS + VBUS clamp |
| C1 (1 nF) | USB-C shield RC to GND |
| R1/R2 (5.1 kΩ) | USB-C CC Rd pulldowns (sink role) |

## Current & power notes

- The **500 mA fuse** bounds USB-powered draw. Eight sensors cold-booting
  simultaneously plus the MCU is the peak load — if powering purely from USB, expect
  the board to stay well under 500 mA in steady ranging, with the highest transient
  during the firmware-download phase.
- Each VL53L8CX draws from **both** rails (AVDD 3.3 V for the analog/VCSEL side,
  IOVDD/CORE 1.8 V for logic). Budget both rails when sizing an external supply.
- For flight use, power the board from the FCU's regulated 5 V and feed **J1**
  (or USB-C), and take the UART off **J7**.
