# Communications & Protocols

The Ascend-8tof system has three communication layers. This page documents each
one exactly as implemented.

```
 VL53L8CX x8 ──I2C(1MHz)──► TCA9548A mux ──I2C──► STM32H563 ──UART(921600)──► VOXL2 ──MPA pipes──► voxl-mapper
   (sensor)                   (0x70)              (firmware)                  (companion)
```

| Link | Physical | Protocol | Speed | Endpoints |
|------|----------|----------|-------|-----------|
| Sensor bus | I²C1 (PB6/PB7) | I²C Fast-mode Plus | **1 MHz** | STM32 ↔ TCA9548A ↔ 8× VL53L8CX |
| Host link | USART2 (PA2 TX) | UART 8N1, ASCII | **≈921 600 baud** | STM32 → VOXL2 |
| Map link | Unix domain sockets | ModalAI MPA (libmodal_pipe) | — | companion → voxl-mapper |

---

## 1. Sensor I²C bus (STM32 ↔ VL53L8CX via TCA9548A)

### Bus parameters
- **Peripheral:** STM32H563 `I2C1`, pins **PB6 = SCL**, **PB7 = SDA**, alternate function AF4.
- **Speed:** **1 MHz (Fast-mode Plus).** `I2C1_TIMINGR = 0x0041132B`
  (PRESC=0, SCLDEL=4, SDADEL=1, SCLH=19 ≈ 312 ns, SCLL=43 ≈ 688 ns) at 64 MHz PCLK1.
  The VL53L8CX is rated for 1 MHz; the TCA9548A is only rated 400 kHz but is
  reliable at 1 MHz in this design.
- **Pull-ups are two-segment** (the mux splits the bus):
  - **Upstream** (STM32 ↔ mux): **R4/R5 = 4.7 kΩ → +3.3 V** on the main board, plus
    STM32 internal pull-ups enabled in firmware. Idle-high = 3.3 V.
  - **Downstream** (mux ↔ each sensor): **R1/R2 = 2.2 kΩ → +1.8 V** on each TOF
    sub-board. **Idle-high = 1.8 V** — expect this level when scoping a sensor's
    SCL/SDA.

### Device addresses
| Device | 7-bit addr | 8-bit addr | Notes |
|--------|-----------|-----------|-------|
| TCA9548A mux | `0x70` | `0xE0` | A0=A1=A2=GND |
| VL53L8CX (all) | `0x29` | `0x52` | Every sensor shares the same address; the mux isolates them |

Because all eight sensors share address `0x29`, only the mux channel(s) currently
selected are electrically on the bus.

### Mux control
The TCA9548A is a single-register device. Writing one byte sets the channel-enable
bitmask (bit *n* = channel *n*):

```c
mux_select(ch):  write TCA9548A(0x70) <- (1 << ch)   // enable one channel
mux_disable():   write TCA9548A(0x70) <- 0x00         // all channels off
```

Multiple bits may be set at once — the firmware uses this to **broadcast** the
identical VL53L8CX firmware image to every detected sensor simultaneously (see
[Firmware → Boot sequence](04-firmware.md#boot-sequence)).

### Register access pattern
The VL53L8CX uses **16-bit register addresses**. The firmware implements four
access primitives (matching ST's reference platform layer):

| Primitive | Direction | Mechanism |
|-----------|-----------|-----------|
| `WrByte` / `WrMulti` | write | START, addr+W, reg[15:8], reg[7:0], data…, STOP |
| `RdByte` / `RdMulti` | read | **Two transactions**: write reg addr **+STOP**, then START addr+R, data…, STOP |

- Reads deliberately use **STOP-then-START** (not repeated START), matching ST's
  reference code.
- Large writes (the ~96 KB firmware download) use the STM32 **RELOAD** mechanism
  so the whole transfer is one logical transaction instead of many 255-byte
  chunks with per-chunk START/STOP overhead.

### Bus recovery
There are **no XSHUT / NRST lines** to the sensors. If a slave hangs holding SDA
low, firmware recovers by:
1. `i2c_recover()` — clear NACK, issue STOP, wait for bus-idle.
2. `i2c_hard_reset()` — bit-bang **up to 16 SCL pulses** on PB6 to clock a stuck
   slave free, manufacture a STOP, then re-initialize the peripheral.

> ⚠️ **Power-cycle after every debug reset / re-flash.** A CPU-only reset leaves
> the sensors mid-transaction and they can hold the bus. Only a full power cycle
> guarantees a clean bus.

---

## 2. Host UART (STM32 → VOXL2)

### Physical
- **Peripheral:** STM32H563 `USART2`, **PA2 = TX** (AF7). RX is enabled in
  firmware but the protocol is one-way (board → host).
- **Connector:** `J7` (4-pin JST GH, `SM04B-GHS-TB`). See
  [Hardware → Connectors](01-hardware.md#connectors).
- **Format:** 8 data bits, no parity, 1 stop bit (**8N1**), no flow control.

### Baud rate — important
The **actual line rate is ≈921 600 baud**, *not* 115 200.

- The USART2 kernel clock is 32 MHz (HSI 64 MHz ÷ 2). Firmware sets `USART2_BRR = 35`,
  giving 32 MHz ÷ 35 = **914 286 baud**, which is **0.79 % below 921 600** — well
  inside UART tolerance, so a 921 600 receiver locks cleanly.
- 921 600 is the fastest rate the VOXL2 GENI UART and common FTDI adapters
  receive reliably. (True 1 Mbaud is exact on this MCU but the receivers can't
  lock it.)
- ⚠️ The firmware boot banner still prints the string `UART 115200` and the
  firmware README's hardware table says `115200` — **both are stale text.**
  Configure your host for **921 600**. The companion service default
  (`uart_baud = 921600`) is correct.

### Wire format (ASCII)
For every sensor with new data, the firmware prints a header line then eight rows
of eight integers. Distances are in **millimetres**; **`0` means invalid / no
return** (the firmware already substitutes 0 for any zone whose
`target_status` isn't 5 or 9 — see [Measurement validity](#measurement-validity)).

```
--- CH<n> ---
 1234  1230  1228 ...   (row 0: 8 space-padded integers, mm)
 ...                    (rows 1..7)
```

- Header: literal `--- CH` followed by the channel digit `0`–`7` and ` ---`.
- Each of the 8 rows: 8 integers, right-aligned in a 6-char field, `\r\n`
  terminated. So each zone value is `distance_mm` or `0`.
- Grid is row-major, 8×8 = 64 zones, in the sensor's own sensor-frame layout.
- Frames stream at the ranging rate (**15 Hz** per sensor); channels are printed
  round-robin as each sensor reports data-ready.

### Reading it directly
```bash
# raw view
python3 ascend-tof8/test/read_tof.py /dev/ttyUSB0    # 921600-8N1

# or any terminal, e.g.
screen /dev/tty.usbserial-XXXX 921600
```

---

## 3. MPA map link (companion → voxl-mapper)

The `voxl-ascend-8tof` companion parses the UART stream, projects each 8×8 grid
into 3-D points, and publishes **one MPA pipe per channel**. See
[VOXL integration](05-voxl-integration.md) for the full data path, packet
formats, extrinsics and voxl-mapper wiring.

Summary of the on-pipe contract:

| chN_format | Packet type | Magic | voxl-mapper slot |
|-----------|-------------|-------|------------------|
| `tof2` | `tof2_data_t` (organized 8×8, ray-cast) | `VOXM` | `tof_pipe_0..3` |
| `point_cloud` | `point_cloud_metadata_t` (unstructured) | `VOXL` | `depth_pipe_0..3` |

Mismatching a pipe's format against the slot it feeds produces
`invalid metadata, magic number=…` in voxl-mapper.

---

## Measurement validity

The firmware emits **`0` for any zone that is not a real measurement**. A zone is
kept only if:
- `nb_target_detected >= 1`, **and**
- `target_status == 5` (range valid) **or** `9` (valid with large pulse).

All other status codes (no/low signal, sigma fail, wrap-around, …) carry a garbage
`distance_mm`, so they are zeroed. Downstream consumers should treat `0` as
"no return", never as "obstacle at 0 mm".
