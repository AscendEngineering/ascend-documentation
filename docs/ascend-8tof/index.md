# Ascend-8tof — System Documentation

Documentation for the **Ascend-8tof** 360° time-of-flight obstacle-sensing system:
a carrier board (STM32H5-family MCU) that reads up to **8× VL53L8CX** 8×8
multizone ToF sensors and streams their measurements as a simple **ASCII distance
stream over UART**. **Any flight controller or onboard computer** can consume it —
this documentation uses a **ModalAI VOXL2** as the worked example integration
because it's the platform we know best, but nothing about the board is
VOXL-specific.

```
 8× VL53L8CX ──► 360° carrier board ──UART(ASCII 8×8)──► any host
  (8×8 grids)     (onboard mux + MCU)                    (FC / onboard computer)
                                                         └─ e.g. VOXL2 + voxl-mapper (example)
```

## Documentation map

| # | Document | Contents |
|---|----------|----------|
| 01 | [Hardware Overview](01-hardware.md) | Boards, sensor, connectors & pinouts, mechanical mounting |
| 02 | [Power](02-power.md) | Input voltage & current range, how to power it |
| 03 | [Communications — UART Output](03-comms-protocol.md) | The ASCII 8×8 distance stream (the interface you consume) |
| 04 | [Firmware](04-firmware.md) | What each firmware variant does and how it's used |
| 05 | [Integration (any host)](05-integration.md) | Host-agnostic recipe + VOXL2/voxl-mapper worked example |
| 06 | [Bring-up & Setup](06-bringup-setup.md) | Assemble → power → verify → integrate → troubleshoot |

## Key facts at a glance

- **Sensors:** up to 8× VL53L8CX, each an **8×8 zone grid at 15 Hz**, forming a
  360° ring.
- **Reliable range:** ~4 m (8×8 mode); ~45° field of view per axis.
- **Power:** single **5 V** input (`J1` or USB-C); < 500 mA typical — see
  [Power](02-power.md).
- **Output:** plain ASCII per-channel **8×8 distance matrices** over UART at
  **≈921 600 baud 8N1** — consumable by any host (see
  [Communications](03-comms-protocol.md#baud-rate-important)).
- **Firmware options:** a **default sensor-stream** firmware (ASCII, stable) or an
  **ACO on-board collision-avoidance** firmware (MAVLink v2 straight to a flight
  controller, **beta**) — see [Firmware](04-firmware.md).
