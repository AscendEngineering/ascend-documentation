# Ascend-8tof v2 — System Documentation

Documentation for the **Ascend-8tof v2** 360° time-of-flight obstacle-sensing
system: a 30 × 30 mm carrier board (STM32H563) reading **8× VL53L8CX** 8×8
multizone ToF sensors and speaking **MAVLink** to a flight controller over a
single UART.

```
 8× VL53L8CX ──► carrier board ──┬── MAVLink OBSTACLE_DISTANCE ──► PX4 collision prevention
  (8×8 grids)   (mux + STM32H5)  │   (always on)
                                 └── 512-zone point cloud ──────► configurator / your host
                                     (on request)
```

## Documentation map

| # | Document | Contents |
|---|----------|----------|
| 01 | [Hardware Overview](01-hardware.md) | Board, connectors & pinouts, channel map, mounting |
| 02 | [Power](02-power.md) | Input voltage limits and how to power it |
| 03 | [Communications](03-comms-protocol.md) | MAVLink output and the binary point-cloud link |
| 04 | [Firmware](04-firmware.md) | Build variants, flashing, diagnostic builds |
| 05 | [Integration](05-integration.md) | PX4 collision prevention + VOXL2 worked example |
| 06 | [Bring-up & Setup](06-bringup-setup.md) | Assemble → power → verify → integrate → troubleshoot |
| 07 | [Obstacle Avoidance (onboard VFH)](07-obstacle-avoidance.md) | The alternative `AVOID=vfh` path, needing the Ascend PX4 fork |

## Key facts at a glance

- **Sensors:** 8× VL53L8CX, each an **8×8 zone grid at 15 Hz**, forming a 360° ring.
- **Reliable range:** ~4 m (8×8 mode); ~45° field of view per axis.
- **Power:** **5 V only** on `J5` pin 1, < 500 mA typical — see [Power](02-power.md).
- **Host link:** one UART at **921 600 8N1** carrying MAVLink (always) and the
  point cloud (on request).
- **Default output:** `OBSTACLE_DISTANCE` (#330) at 10 Hz, 72 bins × 5°, straight
  into **stock PX4 collision prevention** — no custom autopilot build.
- **Mounting:** the tip of the **A** on the lid is the nose = **CH7 (`J8`)**.
- **Configurator:** <https://tools.ascendengineer.com> — live 3D cloud and zone
  masking in Chrome.
