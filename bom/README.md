# Bill of Materials

Exported from the KiCad projects. Two boards make up the system.

- [`main-board-bom.csv`](main-board-bom.csv) — STM32H563 carrier board
  (`oa_pcb_STM32H5_horizontal`).
- [`tof-board-bom.csv`](tof-board-bom.csv) — VL53L8CX sensor sub-board
  (`oa_pcb_TOF_vertical`), one per channel (up to 8).

## Main board — key components

| Ref | Part | Function |
|-----|------|----------|
| IC1 / U1(MCU) | **STM32H563RGT6** | Cortex-M33 host MCU, 64-pin LQFP |
| U3 | **TCA9548A** (TSSOP-24) | 8-channel I²C mux, addr 0x70 |
| U4 | **TPS54360B-Q1** | wide-Vin (60 V) step-down regulator |
| U2 | **TPS62130** | step-down regulator |
| U1 | **USBLC6-2SC6** | USB ESD / data-line protection |
| J2 | USB-C receptacle (USB2.0, 14P) | power / bench |
| J1 | Hirose DF13-02P (2-pin) | external power input |
| J7, J8 | JST GH `SM04B-GHS-TB` (4-pin) | UART / aux |
| J9 | JST GH `SM06B-GHS-TB` (6-pin) | SWD debug |
| J3–J6, J10–J13 | 1 mm 5-pin headers (×8) | TOF sensor connectors (mux CH0–7) |
| Y1 | NX2016SA 25.000 MHz | HSE crystal |
| X1 | NX3215SA 32.768 kHz | LSE (RTC) crystal |
| L1 | NRS4018 2.2 µH | inductor (TPS62130) |
| L2 | NRS6045 10 µH | inductor (TPS54360B) |
| F1 | 500 mA fuse | input protection |
| S1, S2 | TL3780AF tact switches | reset / boot |
| D2 | LED (0805) | status |

## TOF sub-board — components

| Ref | Part | Function |
|-----|------|----------|
| U5 | **VL53L8CXV0GC/1** | 8×8 multizone ToF sensor (LGA-16) |
| R1, R2 | 2.2 kΩ | I²C pull-ups |
| R24, R25, R37, R38 | 47 kΩ | sensor mode-select / bias pulldowns |
| C17 | 4.7 µF | bulk decoupling |
| C30, C49 | 100 nF | decoupling |
| J2 | 1 mm 5-pin header | interface to main board (3V3, 1V8, SCL, SDA, GND) |

See [Hardware](../docs/01-hardware.md) and [Power](../docs/02-power.md) for the
full electrical detail and derived voltages.
