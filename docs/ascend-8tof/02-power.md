# Power

v2 takes a **single 5 V input** on `J5` pin 1 and generates the sensor rails
on-board. You never supply sensor voltages yourself.

!!! danger "5 V only — this changed from v1"
    The earlier vertical board accepted anything from 5 V to a 6S LiPo. **v2 does
    not have a wide-input regulator.** `J5` pin 1 feeds a 3.3 V LDO directly
    through a Schottky diode. Wiring a flight battery to v2 will destroy it.

## Input

| Parameter | Value |
|-----------|-------|
| **Input voltage** | **5 V nominal** |
| **Maximum** | **~5.5 V** — see the limit below |
| Connector | `J5` pin 1 (JST GH 1.25 mm, 4-pin) |
| Typical current | well under **500 mA** in steady ranging |
| Peak current | brief inrush at power-on as all eight sensors initialise |
| Protection | **reverse polarity only** (`D2`, SS14 Schottky in series) |

### Where the limit comes from

The supply chain is short and has no headroom above 5 V:

```
J5.1 ──► D2 (SS14, series Schottky) ──► +5V ──► U3 (TLV75733) ──► +3V3
                                                                    │
                                                                    └─► U1 (TPS62130) ──► +1V8
```

`U3` is a **TLV75733** 3.3 V LDO whose input is rated **5.5 V recommended,
6 V absolute maximum**. Nothing upstream of it clamps or regulates — `D2` is a
plain series diode that only blocks reverse polarity and drops roughly 0.3–0.4 V.
So the LDO sees very nearly whatever you apply to `J5` pin 1.

`U1` (TPS62130) is a wide-input buck, but it is **not** the input stage: it runs
from the 3.3 V rail to produce the sensors' 1.8 V. It does not protect the input.

!!! warning "There is no overvoltage protection"
    `D2` blocks reverse polarity and nothing else — any positive voltage passes
    straight through to a 6 V-max part. This is a known limitation of the current
    revision and is on the list for the next one. Until then, **feed `J5` from a
    regulated 5 V rail**, and check with a meter before plugging in an unfamiliar
    supply.

## Powering it

| Situation | How |
|-----------|-----|
| **Bench** | A USB-UART adapter's 5 V/VCC pin into `J5` pin 1, with its TX/RX/GND on pins 2/3/4. One cable does power and data. |
| **On a vehicle** | A regulated **5 V** rail from the flight-control unit or power module into `J5` pin 1. |

Because `J5` carries power and UART on the same connector, a single 4-wire lead
is all the integration needs. See [Bring-up & Setup](06-bringup-setup.md).

## What the board provides

- Both sensor supplies (**+3V3** and **+1V8**) are generated on-board and
  distributed through the eight sensor connectors.
- `J6` pin 6 is **+3V3**. It is there so a debug probe can sense target voltage —
  do not use it to power the board.
