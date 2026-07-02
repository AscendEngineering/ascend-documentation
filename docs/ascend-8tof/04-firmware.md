# Firmware

The board ships **pre-flashed by Ascend** — you don't build or flash it yourself.
There are **two firmware variants** (same hardware, different behavior and
different UART output). Tell us which you need; this page explains what each one
does and how you use it.

| Variant | UART output | What it does | Status |
|---------|-------------|--------------|--------|
| **Sensor stream** (default) | ASCII 8×8 grids @ ≈921 600 | Streams raw per-sensor distances; **your host** does avoidance/mapping | Stable |
| **ACO** (collision avoidance) | **MAVLink v2** @ 115 200 | Runs obstacle avoidance **on-board** and talks straight to a flight controller | **Beta** |

---

## Sensor-stream firmware (default)

The default firmware reads all connected sensors and continuously streams their
measurements over the host UART as a simple **ASCII 8×8 distance matrix per
sensor** (millimetres; `0` = no return), at **15 Hz** per sensor.

- **Output:** the ASCII stream fully specified in
  [Communications](03-comms-protocol.md).
- **You do the rest:** feed those distances/grids into your own obstacle
  avoidance, mapping (e.g. voxl-mapper), logging, or proximity logic. See
  [Integration](05-integration.md) for a host-agnostic recipe and the VOXL2
  worked example.
- **Best for:** any platform where you want the raw ranging data and control over
  how it's used.

**Behavior notes**
- On power-up the board detects which sensor ports are populated and streams only
  those channels (each labeled `--- CHn ---`).
- Startup takes a couple of seconds while sensors initialize; after that the
  stream is continuous.

---

## ACO Firmware — onboard collision avoidance (beta)

!!! warning "Beta"
    The ACO firmware is **in beta / active development** and not yet fully
    validated against live sensors + a flight controller. Use the default
    sensor-stream firmware for production until it's finalized.

The ACO firmware runs Ascend's **collision-avoidance algorithm on the board
itself** and communicates **MAVLink v2 directly with a flight controller** — no
companion computer required. It turns the sensor into a self-contained obstacle-
avoidance co-processor.

### What it does

1. Receives the vehicle's **odometry** (attitude + velocity) from the flight
   controller over MAVLink.
2. Combines that with the live 8-sensor ToF data to build a **velocity-scaled
   safety envelope** around the vehicle (the faster you fly, the further ahead it
   looks).
3. Detects obstacles entering that envelope and reports them to the flight
   controller as standard **`OBSTACLE_DISTANCE`** messages (full 360°, in 5°
   sectors), so the autopilot's built-in avoidance can act.

### How you use it

- **Wire** the host UART (`J7`) to a spare **TELEM port** on your flight
  controller: board **TX → FC RX**, board **RX ← FC TX**, GND↔GND.
- **Baud:** 115 200, **MAVLink v2**. It presents as an obstacle-avoidance
  component to the autopilot.
- **Enable** your autopilot's obstacle-avoidance / proximity feature (e.g.
  ArduPilot `AVOID_*` / `PRX` parameters) so it consumes the `OBSTACLE_DISTANCE`
  data. No companion computer, no ASCII parsing.

### Status-LED indication

The onboard status LED shows state at a glance:

| Pattern | Meaning |
|---------|---------|
| Fast blink (~100 ms) | collision detected |
| Normal blink (~500 ms) | running, sensors OK |
| Slow blink (~2 s) | no sensors online |

### Beta status

This firmware is still being finalized (mounting-angle calibration, performance
tuning, and full flight validation are in progress). Contact Ascend for current
availability and to have a board flashed with the ACO variant.
