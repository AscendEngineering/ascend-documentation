# Ascend-8tof — System Documentation

Complete documentation for the **Ascend-8tof** 360° time-of-flight obstacle-sensing
system: an STM32-based carrier board that reads up to **8× ST VL53L8CX** ToF
sensors and streams their data to a **ModalAI VOXL2** for 3-D mapping.

```
 8× VL53L8CX ──I2C──► TCA9548A mux ──► STM32H563 ──UART──► VOXL2 ──MPA──► voxl-mapper
  (8×8 grids)          (0x70)          (firmware)          (companion)     (3-D map)
```

## What this covers

| # | Document | Contents |
|---|----------|----------|
| 01 | [Hardware Overview](docs/01-hardware.md) | Boards, MCU, mux, sensor, connectors & pinouts, mechanical |
| 02 | [Power & Voltage Ranges](docs/02-power.md) | Input range, regulators, rails, protection, current budget |
| 03 | [Communications & Protocols](docs/03-comms-protocol.md) | I²C bus, UART wire format, MPA pipes, baud rates, addresses |
| 04 | [STM32 Firmware](docs/04-firmware.md) | Build/flash, boot sequence, peripherals, sensor config |
| 05 | [VOXL Integration](docs/05-voxl-integration.md) | Companion service, packet formats, extrinsics, voxl-mapper wiring |
| 06 | [Bring-up & Setup](docs/06-bringup-setup.md) | Step-by-step: assemble → flash → test → integrate → troubleshoot |

Bill-of-materials CSVs are in [`bom/`](bom/).

## Repositories & source

| Layer | Source location | Notes |
|-------|-----------------|-------|
| PCB (main board) | `pcb/oa_pcb_separated_v2/STM32H56_Board/` | KiCad; `oa_pcb_STM32H5_horizontal.*` |
| PCB (TOF sub-board) | `pcb/oa_pcb_separated_v2/TOF_Board/` | KiCad; `oa_pcb_TOF_vertical.*` |
| STM32 firmware | `Downloads/ascend-tof8/` | bare-metal C, git repo |
| VOXL companion | `Downloads/voxl-ascend-8tof/` | VOXL-SDK service, git repo |

## Key facts at a glance

- **MCU:** STM32H563RGT6 (Cortex-M33, 64 MHz HSI, no HAL).
- **Sensors:** up to 8× VL53L8CX, each an 8×8 zone grid at **15 Hz**, shared I²C
  address `0x29`, isolated by a **TCA9548A** mux (`0x70`).
- **Sensor bus:** I²C1 (PB6/PB7) at **1 MHz** Fast-mode Plus.
- **Host link:** USART2 TX (PA2), ASCII grids at **≈921 600 baud 8N1**
  (⚠️ *not* 115 200 — the firmware banner text is stale; see
  [comms](docs/03-comms-protocol.md#baud-rate--important)).
- **Reliable range:** ~4 m (VL53L8CX 8×8 mode).
- **Output to VOXL:** one MPA pipe per channel (`tof2` or `point_cloud`), placed by
  voxl-mapper via `extrinsics.conf`.

## How to read / host this

These are plain Markdown files — they render on GitHub/GitLab, in VS Code preview,
or any Markdown viewer, with **no build step**. To publish later:

- **GitLab/GitHub Pages:** push this folder; enable Pages (or drop in an MkDocs/
  Docusaurus config to get a searchable site — the file numbering is already
  nav-ready).
- **Offline share:** open `README.md` and follow the links, or export any file to
  PDF (e.g. `pandoc docs/*.md -o ascend-8tof.pdf`).

> **Status note:** electrical values (input voltage range, per-rail voltages,
> and full J7/J8/J9 pinouts) in [02-power](docs/02-power.md) and
> [01-hardware](docs/01-hardware.md) are derived directly from the KiCad
> schematic and BOM. Where a value was computed from a feedback-divider, the math
> is shown so you can double-check against the board.
