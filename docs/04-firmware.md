# STM32 Firmware (`ascend-tof8`)

Bare-metal firmware for the main board's **STM32H563RGT6** (Cortex-M33, 64 MHz HSI,
**no HAL** — direct register access). It brings up as many of the 8 VL53L8CX
sensors as are present, streams each sensor's 8×8 distance grid over UART.

- **Source:** `ascend-tof8/` (`main.c` + `uld/` ST ULD driver + `startup_stm32h563xx.s`).
- **Target:** STM32H563RGT6, 64-pin LQFP.
- **Clock:** HSI 64 MHz, no PLL/external oscillator used by firmware (the HSE/LSE
  crystals are populated on the board but not required by this firmware).

## Toolchain & build

Requires `arm-none-eabi-gcc` and OpenOCD.

```bash
make            # build, UART output (default)
make flash      # flash via ST-Link + OpenOCD
make run        # build with semihosting, flash, run (Ctrl-C to stop)
make clean      # remove build artifacts
```

- **Flash target / linker:** `STM32H563RGTx_FLASH.ld`.
- **Debug adapter:** ST-Link via `openocd.cfg`.
- **`SEMIHOSTING` build flag:** routes `printf`-style output through the ST-Link/
  OpenOCD console instead of UART (used by `make run`).

> ⚠️ **Always power-cycle the board after flashing.** A debug reset leaves the
> I²C sensors holding the bus; there are no XSHUT/NRST lines to release them.

## Peripheral map

| Peripheral | Pins | Config |
|-----------|------|--------|
| USART2 | PA2 (TX), (PA3 RX enabled, unused) | 8N1, `BRR=35` → ≈921 600 baud, AF7 |
| I2C1 | PB6 (SCL), PB7 (SDA) | 1 MHz Fm+, `TIMINGR=0x0041132B`, AF4, internal pull-ups on |
| ICACHE | — | disabled (`ICACHE_CR = 0`) |
| Clock | HSI | 64 MHz; USART2 kernel clock 32 MHz (HSI/2) |

Constants: `TCA9548A_ADDR 0x70`, `NUM_SENSORS 8`, `I2C_TIMEOUT 200000`,
`VL53L8CX_DEFAULT_I2C_ADDRESS 0x52` (8-bit).

## Boot sequence

Cold boot takes **≈1.7 s per detected sensor** — the VL53L8CX firmware download
(~96 KB at 1 MHz I²C) dominates.

1. **Core init** — disable ICACHE, wait `HSIRDY`, enable GPIOA/GPIOB clocks.
2. **`uart_init()`** — USART2 up, banner printed.
3. **`i2c_init()`** — I2C1 up at 1 MHz.
4. **Mux presence check** — write `0x00` to TCA9548A (`0x70`). If it NAKs, print
   `ERROR: TCA9548A mux not responding!` and halt (power-cycle needed).
5. **Phase 1 — channel scan.** For each channel 0–7: select it on the mux, read
   VL53L8CX **device-ID register `0x0000`**; a value of **`0xF0`** marks a sensor
   present. Builds `ch_mask` of detected channels.
6. **Phase 2 — broadcast firmware download** (`broadcast_reboot_and_fw`). The mux
   enables **all detected channels at once** and the identical VL53L8CX firmware
   image is written to every sensor in one pass (they're in identical state, so
   register reads wired-AND correctly). This is the key speed optimization — the
   ~96 KB image is sent once, not 8 times.
7. **Phase 3 — per-sensor init** (`vl53l8cx_init` + `sensor_post_fw_init`). Done
   individually because NVM calibration data is unique per sensor:
   - firmware CRC check (`0x0C0B6C9E`),
   - NVM offset data load, default cross-talk, default configuration,
   - set resolution **8×8**, ranging frequency **15 Hz**, `start_ranging`.
   On failure the channel is skipped after an `i2c_hard_reset()`.
8. **Main loop** — round-robin over active channels: `mux_select`,
   `check_data_ready`, and when ready `get_ranging_data` → `print_grid` over UART.
   5 ms pacing delay per loop.

Startup log (over UART/semihosting) looks like:

```
========================================
  ascend-tof8 -- VL53L8CX ranging
========================================
UART 115200 | I2C 1MHz Fm+          <- NOTE: stale text; real rate ≈921600
TCA9548A: OK
Scanning channels...
  CH0: detected
  CH1: --
  ...
Broadcast FW download (0x...)...
  FW broadcast... done
  OK
Initializing sensors...
  CH0: OK
  ...
N/8 sensors active.
```

## Sensor configuration (as flashed)

| Setting | Value |
|---------|-------|
| Resolution | 8×8 (64 zones) |
| Ranging frequency | 15 Hz |
| Ranging mode | single-shot pipe (`VL53L8CX_DCI_SINGLE_RANGE`) |
| Targets per zone | 1 (`VL53L8CX_NB_TARGET_PER_ZONE`) |
| Valid `target_status` | 5 or 9 (others → distance forced to 0) |

## Design notes / gotchas (from firmware comments)

- **Power-cycle after flashing** — I²C slaves hold the bus after a debug reset;
  no XSHUT/NRST to release them.
- **TCA9548A RESET pull-up must go to 3.3 V, not 1.8 V.** Mux V_CC is 3.3 V so
  V_IH = 2.31 V; a 1.8 V pull-up leaves RESET in the undefined region.
- **I²C at 1 MHz** — above the TCA9548A's 400 kHz rating but reliable here.
- **VL53L8CX NCS** tied to GND via a 47 kΩ pulldown selects **I²C mode** (per
  datasheet).
- **STOP+START reads** (two transactions) rather than repeated-START, matching
  ST's reference platform.
- **RELOAD-based large writes** make the firmware download a single transaction.

## Bench test script

`ascend-tof8/test/read_tof.py [port]` opens the UART (default
`/dev/tty.usbserial-1110`, 921600-8N1), prints the incoming grids, and
auto-reconnects across power cycles. Use it to confirm the board before wiring it
to the VOXL2.
