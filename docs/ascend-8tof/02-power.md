# Power

The board takes a **single DC input over a wide range** and regulates everything
the sensors need on-board — you don't supply any sensor voltages yourself.

## Input

Power the board from **either** input:

| Input | Connector | Range | Use |
|-------|-----------|-------|-----|
| **External DC** | `J1` (2-pin) | **5 V – 6S LiPo (~25 V)** | Flight / integration — feed from a 5 V rail *or* directly from the vehicle battery (2S–6S) |
| **USB-C** | `J2` | 5 V | Bench / desktop |
| **UART 5 V** | `J7` pin 1 | 5 V | Power over the host UART connector — e.g. from a USB-UART adapter's 5 V/VCC pin |

All three are diode-OR'd onto the input — you can safely have more than one
connected (the higher source supplies, the others are blocked).

| Parameter | Value |
|-----------|-------|
| **Input voltage** | **5 V to ~25.2 V** (up to a **6S LiPo**), via `J1` |
| **Typical current** | well under **500 mA** in steady ranging |
| **Peak current** | brief inrush at power-on (all sensors initializing) |
| Protection | reverse-polarity protected; USB path is fused + diode-isolated from the DC input |

!!! note "Wide input"
    `J1` accepts anything from **5 V up to a 6S LiPo** — an on-board wide-input
    regulator converts it down to the rails the sensors run on. You can feed it a
    regulated 5 V or wire it straight to the flight battery. USB-C (`J2`) is a 5 V
    bench alternative; you don't need both.

## What the board provides

- All sensor supplies are generated **on-board** from the DC input — you do
  **not** provide anything to the sensors directly; they're powered through the 8
  sensor connectors.
- The host UART connector (`J7`) includes a **+5 V pin you can power the board
  from** — handy when you're already connected with a USB-UART adapter (wire its
  5 V/VCC into `J7` pin 1). It's a power input, not an output.

## Powering for flight

Feed `J1` from your flight-control unit / power module — either a regulated 5 V
rail or the vehicle battery directly (up to **6S**) — and take the data connection
off the host UART (`J7`). See [Bring-up & Setup](06-bringup-setup.md).
