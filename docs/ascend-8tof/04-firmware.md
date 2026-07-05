# Firmware

The board ships **pre-flashed by Ascend**. You do not build or flash it yourself.
There are **two firmware variants** (same hardware, different behavior and different UART output). Tell us which you need. This page states what each one does and how to use it.

| Variant | UART output | What it does | Status |
|---------|-------------|--------------|--------|
| **Sensor stream** (default) | ASCII 8×8 grids @ ≈921 600 | Streams raw per-sensor distances, **your host** performs avoidance and mapping | Stable |
| **ACO** (collision avoidance) | **MAVLink v2** @ 115 200 | Runs obstacle avoidance **on-board** and communicates directly with a flight controller | **Beta** |

---

## Sensor-stream firmware (default)

The default firmware reads all connected sensors and continuously streams their measurements over the host UART as a simple **ASCII 8×8 distance matrix per sensor** (millimetres, `0` = no return), at **15 Hz** per sensor.

- **Output:** the ASCII stream specified in
  [Communications](03-comms-protocol.md).
- **Host processing:** feed the distances or grids into your own obstacle avoidance, mapping (e.g. voxl-mapper), logging, or proximity logic. See
  [Integration](05-integration.md) for a host-agnostic recipe and the VOXL2 worked example.
- **Best for:** platforms that require raw ranging data and control over how it is used.

**Behavior notes**
- On power-up the board detects populated sensor ports and streams only those channels (each labeled `--- CHn ---`).
- Startup takes a few seconds while sensors initialize. After initialization the stream is continuous.

---

## ACO firmware: onboard collision avoidance (beta)

!!! warning "Beta"
    The ACO firmware is **in beta / active development** and not yet fully validated against live sensors and a flight controller. Use the default sensor-stream firmware for production until it is finalized.

The ACO firmware runs Ascend's **collision-avoidance algorithm on the board itself** and communicates **MAVLink v2 directly with a flight controller**. No companion computer is required. It operates as a self-contained obstacle-avoidance co-processor.

### What it does

1. Receives the vehicle's **odometry** (attitude + velocity) from the flight controller over MAVLink.
2. Combines this with live 8-sensor ToF data to build a **velocity-scaled safety envelope** around the vehicle. Faster motion increases the forward look distance.
3. Detects obstacles entering that envelope and reports them to the flight controller as standard **`OBSTACLE_DISTANCE`** messages (full 360°, in 5° sectors), enabling the autopilot's built-in avoidance.

### How you use it

- **Wire** the host UART (`J7`) to a spare **TELEM port** on your flight controller: board **TX → FC RX**, board **RX ← FC TX**, GND↔GND.
- **Baud:** 115 200, **MAVLink v2**. It presents as an obstacle-avoidance component to the autopilot.
- **Enable** the autopilot obstacle-avoidance or proximity feature (e.g. ArduPilot `AVOID_*` or `PRX` parameters) so it consumes the `OBSTACLE_DISTANCE` data. No companion computer or ASCII parsing is required.

### Beta status

This firmware is under active development, including mounting-angle calibration, performance tuning, and full flight validation. Contact Ascend for availability and to have a board flashed with the ACO variant.
