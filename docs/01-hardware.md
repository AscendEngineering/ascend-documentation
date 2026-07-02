# Hardware Overview

The Ascend-8tof hardware is **two board types**:

1. **Main / carrier board** (`oa_pcb_STM32H5_horizontal`) — STM32H563 MCU, TCA9548A
   I²C mux, power supplies, USB-C, and the 8 sensor connectors.
2. **TOF sub-board** (`oa_pcb_TOF_vertical`) — one small board per channel carrying
   a single VL53L8CX sensor. Up to 8 plug into the main board.

> **Reference-designator note:** on the main board the MCU is **`IC1`**
> (STM32H563RGT6). `U1` is the **USBLC6-2SC6** USB-protection array — not the MCU.
> Regulators: `U2` = TPS62130 (1.8 V), `U3` = TCA9548A (mux), `U4` = TPS54360B (3.3 V).

See [Power & Voltage Ranges](02-power.md) for the supply detail and
[Communications](03-comms-protocol.md) for the bus protocols. Full parts lists are
in the repository's `bom/` folder.

## Main board — major devices

| Ref | Part | Role |
|-----|------|------|
| IC1 | STM32H563RGT6 (LQFP-64) | Host MCU, Cortex-M33 @ 64 MHz HSI |
| U3 | TCA9548A (TSSOP-24) | 8-channel I²C mux, addr **0x70** |
| U4 | TPS54360B-Q1 | Buck → **+3V3** rail (from +5V bus) |
| U2 | TPS62130 | Buck → **+1V8** rail (from +3V3) |
| U1 | USBLC6-2SC6 | USB D± ESD/TVS + VBUS clamp |
| Y1 | NX2016SA 25.000 MHz | HSE crystal (PH0/PH1) |
| X1 | NX3215SA 32.768 kHz | LSE / RTC crystal (PC14/PC15) |
| S1 | tact switch | **BOOT0** (press → system bootloader) |
| S2 | tact switch | **NRST** reset |
| D2 | LED | **1.8 V power-good** indicator (driven by U2 PG) |

## STM32H563 (IC1) pin map

| Function | Pin(s) | Detail |
|----------|--------|--------|
| I²C1 → mux | PB6 (SCL), PB7 (SDA) | AF4; on-board pull-ups **R4/R5 = 4.7 kΩ → +3V3** |
| USART2 → J7 | PA2 (TX), PA3 (RX) | AF7; host serial link |
| USB FS → J2 | PA11 (DM), PA12 (DP) | via U1 USBLC6 |
| SWD → J9 | PA13 (SWDIO), PA14 (SWCLK), PB3 (SWO) | debug |
| NRST | pad 7 | S2 button + 100 nF (C27) + J9 pin5 |
| BOOT0 | pad 60 | R7 = 10 kΩ pulldown + S1 to +3V3 |
| HSE | PH0/PH1 | Y1 25 MHz + C9/C10 (5.6 pF) — *not used by current firmware (HSI)* |
| LSE | PC14/PC15 | X1 32.768 kHz + C13/C14 (5.1 pF) |
| Core VCAP | pad 30, 62 | C19/C23 (2.2 µF) |
| VDD / VSS | 3V3 / GND | standard |

> The current firmware runs on the internal **HSI (64 MHz)** and does not enable
> the HSE/LSE crystals, though they are populated.

## I²C mux (TCA9548A, U3)

- **Address:** A0=A1=A2=GND → **0x70**.
- **Upstream:** VCC = +3V3; SCL/SDA = STM32 PB6/PB7 (shared R4/R5 4.7 kΩ pull-ups
  to +3V3).
- **RESET (active-low):** pulled high by **R8 = 10 kΩ → +3V3**. **No MCU GPIO drives
  it** — the mux is never actively reset in firmware (bus recovery is done by
  bit-banging SCL instead). The 3.3 V pull-up is required: mux V_CC is 3.3 V so
  V_IH ≈ 2.31 V — a 1.8 V pull-up would leave RESET in the undefined region.
- **8 downstream channels** route to the 8 sensor connectors (table below).

## Connectors

### Power & host

| Ref | Type | Purpose | Pinout |
|-----|------|---------|--------|
| **J1** | Hirose DF13-02P (2-pin) | External DC power input | 1 = V+ (→ +5V bus via CR1), 2 = GND |
| **J2** | USB-C receptacle (USB2.0) | Power + USB FS data | VBUS (fused via F1) → +5V; D+ = PA12, D− = PA11 (via U1); CC1/CC2 = Rd 5.1 kΩ (sink) |
| **J7** | JST GH SM04B (4-pin) | **USART2 serial** | 1 = +5 V (via D3), 2 = RX (PA3), 3 = TX (PA2), 4 = GND |
| **J8** | JST GH SM04B (4-pin) | Secondary GPIO/UART | 1 = NC, 2 = PB15, 3 = PB14, 4 = GND |
| **J9** | JST GH SM06B (6-pin) | **SWD debug** | 1 = GND, 2 = SWO, 3 = SWDIO, 4 = SWCLK, 5 = NRST, 6 = +3V3 |

> **J7 is the flight/host UART.** Wire pin 3 (board TX) to the VOXL2/adapter RX,
> pin 4 to GND. Pin 1 exposes +5 V (diode-isolated) if you want to power a small
> adapter — do **not** back-feed it.

### TOF sensor connector (×8)

All eight sensor connectors (`J3, J4, J5, J6, J10, J11, J12, J13`) are identical
5-pin 1.00 mm headers:

| Pin | Signal |
|-----|--------|
| 1 | **+3V3** (AVDD) |
| 2 | **+1V8** (IOVDD / CORE_1V8) |
| 3 | **SCL** (mux SCn) |
| 4 | **SDA** (mux SDn) |
| 5 | **GND** |

Each connector's SCL/SDA go to one TCA9548A channel — **this mapping fixes each
sensor's channel number, which in turn fixes its bearing in software**:

| Connector | Mux channel | Connector | Mux channel |
|-----------|-------------|-----------|-------------|
| **J6** | CH0 | **J12** | CH4 |
| **J5** | CH1 | **J13** | CH5 |
| **J4** | CH2 | **J10** | CH6 |
| **J3** | CH3 | **J11** | CH7 |

## TOF sub-board (`oa_pcb_TOF_vertical`)

One VL53L8CX (`U5`, LGA-16) per board, plus decoupling, I²C pull-ups and mode straps.

| Item | Detail |
|------|--------|
| Interface | 5-pin header **J2**: 1=+3V3, 2=+1V8, 3=SCL, 4=SDA, 5=GND (matches main-board sensor connector) |
| AVDD | **+3.3 V**, decoupled by C17 (4.7 µF) |
| IOVDD | **+1.8 V**, decoupled by C49 (100 nF) |
| CORE_1V8 | **+1.8 V**, decoupled by C30 (100 nF) |
| I²C pull-ups | **R1/R2 = 2.2 kΩ → +1.8 V (IOVDD)** — SDA=R1, SCL=R2 |
| NCS | **R24 = 47 kΩ → GND** (selects I²C mode) |
| SPI_I2C_N | **R25 = 47 kΩ → GND** (selects I²C interface) |
| LPn | **R38 = 47 kΩ → +1.8 V** (device enabled) |
| SYNC | **R37 = 47 kΩ → +1.8 V** |
| INT / GPIO1 | not connected (interrupt unused; firmware polls) |
| I²C address | fixed default 7-bit **0x29** (8-bit 0x52); no address-strap hardware |

> ⚠️ **Two-segment pull-ups.** The STM32↔mux (upstream) segment is pulled to
> **3.3 V** (R4/R5 on the main board); each mux↔sensor (downstream) segment is
> pulled to **1.8 V** (R1/R2 on the sub-board). This is fine — the mux isolates the
> segments — but it means when you scope a sensor's I²C lines the idle-high level
> is **1.8 V, not 3.3 V**.

## Mechanical / mounting

- Board is mounted flat on top of the flight-control unit (FCU) with **CH3 (J3)
  facing the drone nose**; the 8 sensors then look outward in ~45° increments to
  form a 360° ring. See the bearing/extrinsics table in
  [VOXL integration](05-voxl-integration.md#extrinsics-etcmodalaiextrinsicsconf).
- Sensors sit ~3 cm from the FCU center — negligible translation at meter-scale
  mapping, so extrinsic translations default to zero.
