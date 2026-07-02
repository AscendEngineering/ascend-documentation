# Ascend-8tof — System Documentation

Complete documentation for the **Ascend-8tof** 360° time-of-flight obstacle-sensing
system: an STM32-based carrier board that reads up to **8× ST VL53L8CX** ToF
sensors and streams their measurements as a simple **ASCII distance stream over
UART**. **Any flight controller or onboard computer** can consume it — this
documentation uses a **ModalAI VOXL2** as the worked example integration because
it's the platform we know best, but nothing about the board is VOXL-specific.

```
 8× VL53L8CX ──I2C──► TCA9548A mux ──► STM32H563 ──UART(ASCII)──► any host
  (8×8 grids)          (0x70)          (firmware)                 (FC / onboard computer)
                                                                  └─ e.g. VOXL2 + voxl-mapper (example)
```

## Documentation map

| # | Document | Contents |
|---|----------|----------|
| 01 | [Hardware Overview](01-hardware.md) | Boards, MCU, mux, sensor, connectors & pinouts, mechanical |
| 02 | [Power & Voltage Ranges](02-power.md) | Input range, regulators, rails, protection, current budget |
| 03 | [Communications & Protocols](03-comms-protocol.md) | I²C bus, UART wire format (the universal interface), baud rates, addresses |
| 04 | [STM32 Firmware](04-firmware.md) | Build/flash, boot sequence, peripherals, sensor config |
| 05 | [Integration (any host)](05-integration.md) | Host-agnostic recipe + VOXL2/voxl-mapper worked example |
| 06 | [Bring-up & Setup](06-bringup-setup.md) | Step-by-step: assemble → flash → test → integrate → troubleshoot |

Bill-of-materials CSVs and a parts summary are in the `bom/` folder of the repo.

## Key facts at a glance

- **MCU:** STM32H563RGT6 (Cortex-M33, 64 MHz HSI, no HAL).
- **Sensors:** up to 8× VL53L8CX, each an 8×8 zone grid at **15 Hz**, shared I²C
  address `0x29`, isolated by a **TCA9548A** mux (`0x70`).
- **Sensor bus:** I²C1 (PB6/PB7) at **1 MHz** Fast-mode Plus.
- **Host link:** USART2 TX (PA2), ASCII grids at **≈921 600 baud 8N1**
  (⚠️ *not* 115 200 — the firmware banner text is stale; see
  [Communications](03-comms-protocol.md#baud-rate-important)).
- **Reliable range:** ~4 m (VL53L8CX 8×8 mode).
- **Output:** plain ASCII per-channel 8×8 grids over UART — consumable by any host.
  (The VOXL2 example republishes them as one MPA pipe per channel for voxl-mapper.)

## Source repositories

| Layer | Source location |
|-------|-----------------|
| PCB — main board | `pcb/oa_pcb_separated_v2/STM32H56_Board/` (KiCad) |
| PCB — TOF sub-board | `pcb/oa_pcb_separated_v2/TOF_Board/` (KiCad) |
| STM32 firmware | `ascend-tof8/` (bare-metal C) |
| VOXL companion | `voxl-ascend-8tof/` (VOXL-SDK service) |
