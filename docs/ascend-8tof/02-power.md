# Power

The board accepts a single DC input over a wide range and regulates the rails the sensors require on board. You do not supply sensor voltages.

## Input

Power the board from either input:

| Input | Connector | Range | Use |
|-------|-----------|-------|-----|
| **External DC** | `J1` (2-pin) | **5 V to 6S LiPo (~25 V)** | Flight / integration, feed from a 5 V rail or directly from the vehicle battery (2S to 6S) |
| **USB-C** | `J2` | 5 V | Bench / desktop |
| **UART 5 V** | `J7` pin 1 | 5 V | Power over the host UART connector, for example from a USB-UART adapter's 5 V/VCC pin |

All three inputs are diode ORed onto the input. You can connect more than one at the same time. The higher source supplies and the others are blocked.

| Parameter | Value |
|-----------|-------|
| **Input voltage** | **5 V to ~25.2 V** (up to a **6S LiPo**), via `J1` |
| **Typical current** | well under **500 mA** in steady ranging |
| **Peak current** | brief inrush at power on (all sensors initializing) |
| Protection | reverse polarity protected, USB path is fused + diode isolated from the DC input |

!!! note "Wide input"
    `J1` accepts anything from **5 V up to a 6S LiPo**. An on board wide input regulator converts it to the rails the sensors use. You can feed a regulated 5 V or wire it directly to the flight battery. USB-C (`J2`) is a 5 V bench alternative. You do not need both.

## What the board provides

- All sensor supplies are generated on board from the DC input. You do not provide anything to the sensors directly. They are powered through the 8 sensor connectors.
- The host UART connector (`J7`) includes a +5 V pin that can power the board. This is useful when connected with a USB-UART adapter, wire its 5 V/VCC into `J7` pin 1. It is a power input, not an output.

## Powering for flight

Feed `J1` from your flight control unit or power module, either a regulated 5 V rail or the vehicle battery directly (up to **6S**). Take the data connection from the host UART (`J7`). See [Bring-up & Setup](06-bringup-setup.md).
