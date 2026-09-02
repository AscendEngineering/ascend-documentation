# Bring-up & Setup Guide

Boards in a box → a working obstacle sensor on your vehicle. Boards ship
**pre-flashed** with your chosen [firmware variant](04-firmware.md); the build
and flash steps here are only needed if you are changing it.

## 0. What you need

- Ascend-8tof v2 carrier board + 8 TOF sub-boards.
- A **regulated 5 V** supply for `J5` pin 1 — **not** a flight battery, see
  [Power](02-power.md).
- A 921 600-capable **USB-UART adapter** for bench work. Its 5 V/VCC can power
  the board through `J5` pin 1, so one 4-wire lead does power and data.
- An **ST-Link** on `J6` only if you need to reflash.
- Chrome, for the [configurator](https://tools.ascendengineer.com).

## 1. Assemble

Plug each sub-board into its sensor port. The port fixes the channel, and the
channel fixes the bearing:

| Channel | Port | Direction | Channel | Port | Direction |
|---------|------|-----------|---------|------|-----------|
| **CH7** | **`J8`** | **FRONT / nose** | CH3 | `J1` | back |
| CH0 | `J4` | front-right | CH4 | `J9` | back-left |
| CH1 | `J3` | right | CH5 | `J10` | left |
| CH2 | `J2` | back-right | CH6 | `J7` | front-left |

Seat every connector fully before powering. Mount the unit with the **tip of the
"A" facing the vehicle nose** — that is CH7.

## 2. Power and verify

1. Wire the adapter to `J5`: **board TX (pin 3) → adapter RX**, **adapter TX →
   board RX (pin 2)**, GND↔GND, and 5 V to pin 1 if powering this way.

    Both directions must be connected. The point cloud is gated on the board
    hearing from a host (see
    [Communications](03-comms-protocol.md#why-a-passive-listener-sees-only-mavlink)),
    so TX-only wiring will never show you a cloud.

2. Open the [configurator](https://tools.ascendengineer.com) in Chrome and
   connect, **or** run:

    ```bash
    python3 tools/tof8-stream.py          # live 8×8 grids
    python3 tools/tof8-poll.py            # link health, which channels range
    ```

3. Wave a hand ~30 cm from the nose sensor. **CH7**'s grid should drop to ~300 mm.
   If a different channel lights up, the unit is not mounted nose-forward.

**Sanity checks**

- The onboard LED is a **power-good indicator only** — rails are up. It says
  nothing about sensors or data.
- Zones with no return read as no data, **not** "obstacle at 0 mm".
- A missing channel points at that sub-board or its connector — but read the
  next section before concluding the mux is bad.

## 3. Reflashing (optional)

```bash
AVOID=cp BOARD=horiz3 ./tools/flash-board.sh
```

Expect `sensors : 8/8` / `ALL 8 CHANNELS OK`. If it reports `0/8`, **power-cycle
the board and re-check** before believing it:

```bash
./tools/read-sensors.sh     # reads a running board without resetting it
```

A reset does not clear the multiplexer's channel latch, so a bus jammed before
flashing stays jammed through the flash.

## A sensor that jams the bus

This failure mode is worth understanding because **the error message points at
the wrong part**.

A VL53L8CX that holds SDA low drags down the whole shared bus the instant the
multiplexer connects it. From the MCU's side that is indistinguishable from a
dead multiplexer, so bring-up reports *every* channel as
`mux never answered (check U2)` — including seven healthy ones.

Firmware cannot recover from it. Clearing the TCA9548A's channel latch requires
a bus transaction, and the bus is exactly what is jammed; `U2`'s `RESET` is only
pulled up by `R6`, not driven by a GPIO. **Only a power cycle clears it.**

### Locating the bad sensor

```bash
# 1. ascending walk
make BOARD=horiz3 AVOID=cp DIAG=1 && DIAG=1 ./tools/flash-board.sh
#    POWER-CYCLE the board, then:
DIAG=1 ./tools/read-diag.sh

# 2. descending walk
make BOARD=horiz3 AVOID=cp DIAG=1 DIAGDIR=down && DIAG=1 DIAGDIR=down ./tools/flash-board.sh
#    POWER-CYCLE again, then:
DIAGDIR=down ./tools/read-diag.sh
```

The walk samples SCL/SDA **before anything drives them**, then enables one
channel at a time:

```
cold SCL   : HIGH (idle, healthy)
cold SDA   : HIGH (idle, healthy)
mux @ 0x70 : ACK
first bad  : CH4

  CH0 (J4) front-right   clean, sensor ACKed at 0x29
  ...
  CH4 (J9) back-left     SDA PULLED LOW  <-- this channel jams the bus
```

Reading the result:

- **cold SDA LOW** — no sensor can be responsible; the multiplexer comes out of
  reset with every channel disconnected. The fault is on the main segment: the
  MCU pin, `R3`, `U2`'s upstream side, or a short.
- **cold SDA HIGH** — the bus is fine at rest, and the walk names the culprit.

!!! warning "Run the walk in both directions"
    Once a channel jams the bus, every later `select` silently does nothing and
    the multiplexer stays latched on the culprit — so channels *after* it are
    **indeterminate, not bad**. The tool labels them as such. Only channels that
    fail in both directions are genuinely bad.

### Keeping the board usable

```bash
make BOARD=horiz3 AVOID=cp EXCLUDE=4 && EXCLUDE=4 ./tools/flash-board.sh
```

The excluded channel is never selected, so the remaining seven work normally.
This is a stopgap — replace the sensor when you can.

## Other failure signatures

| Symptom | Meaning |
|---------|---------|
| `mux never answered` on **all 8** | Usually one sensor jamming the bus, not a dead `U2`. Run the walk above. |
| `firmware download failed` on one channel | Sensor ACKs at `0x29` and passes `is_alive()` but cannot take the ~85 KB firmware load. Points at the part or a marginal joint, not the bus. Swap that sensor with a known-good one to confirm. |
| `sensor did not answer` on one channel | Nothing on that connector — check the sub-board and seating. |
| `start_ranging failed` | Usually supply current — check the 5 V rail under load. |

A quick way to separate a bad sensor from a bad board position: **swap the
suspect sub-board with a known-good one.** If the fault follows the part, replace
it; if it stays on the connector, it is board-side.

## 4. Integrate

See [Integration](05-integration.md) for the PX4 collision-prevention path
(`AVOID=cp`, the default) and the VOXL2 worked example.

## Troubleshooting quick-reference

| Symptom | Likely cause / fix |
|---------|--------------------|
| MAVLink visible, no point cloud | Expected. The cloud is gated — you must send a keepalive. Use `tof8-stream.py` or the configurator. |
| Nothing at all on the UART | Baud (**921 600-8N1**), or board TX → adapter RX reversed. |
| Cannot open the port | Something else owns it — configurator tab, `screen`, or `mavlink-router`. On a VOXL2, PX4's `mavlink` owns `/dev/ttyHS1`. |
| Configurator will not connect | Web Serial needs HTTPS and Chrome. |
| `0/8` right after flashing | Power-cycle and re-check with `read-sensors.sh` — a reset does not clear the mux latch. |
| Obstacle appears in the wrong direction | Unit not mounted nose-forward. On v2 the nose is **CH7 (`J8`)**, not CH3. |
