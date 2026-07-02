# Power

The board regulates everything the sensors need internally — you only supply a
single DC input.

## Input

Power the board from **either** input (they're interchangeable):

| Input | Connector | Use |
|-------|-----------|-----|
| External DC | `J1` (2-pin) | Flight / integration — feed from your vehicle's regulated 5 V |
| USB-C | `J2` | Bench / desktop |

| Parameter | Value |
|-----------|-------|
| **Input voltage** | **5 V nominal** (recommended operating range **5.0–5.5 V**) |
| **Typical current** | well under **500 mA** in steady ranging |
| **Peak current** | brief inrush at power-on (all sensors initializing) — size the supply for ≥ 500 mA |
| Protection | reverse-polarity and over-current protected |

!!! warning "Use a 5 V supply"
    Feed `J1` with a regulated **5 V** rail. Do not exceed the recommended range —
    the board is designed around a 5 V input, and higher voltages are not
    supported on the input net.

## What the board provides

- All sensor supplies are generated on-board from the 5 V input — you do **not**
  provide anything to the sensors directly; they're powered through the 8 sensor
  connectors.
- The host UART connector (`J7`) also exposes a protected **+5 V** pin for
  conveniently powering a small USB-UART adapter. Treat it as an output only —
  do not back-feed power into it.

## Powering for flight

Take a regulated **5 V** feed from the flight-control unit / power module to `J1`,
and take the data connection off the host UART (`J7`). See
[Bring-up & Setup](06-bringup-setup.md).
