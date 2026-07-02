# Bring-up & Setup Guide

End-to-end procedure to go from bare boards to obstacles appearing in voxl-mapper.

## 0. What you need

- Ascend main board (STM32H563) + up to 8 TOF sub-boards (VL53L8CX).
- 8× 5-pin 1 mm sensor cables (main-board `J3/J4/J5/J6/J10/J11/J12/J13` → TOF `J2`).
- ST-Link (SWD via `J9`) + `arm-none-eabi-gcc` + OpenOCD for flashing.
- USB-C cable **or** a regulated supply on the `J1` power input
  (see [Power](02-power.md) for the allowed input range).
- USB-UART adapter (921 600-capable, e.g. FTDI) for bench test, wired to `J7`.
- For flight integration: a VOXL2 with VOXL-SDK.

## 1. Assemble & connect

1. Plug each TOF sub-board into a main-board sensor connector with the 5-pin
   cable. Note the **channel↔connector map** — it determines each sensor's
   bearing in software:

   | Mux CH | Connector | Mux CH | Connector |
   |--------|-----------|--------|-----------|
   | 0 | J6 | 4 | J12 |
   | 1 | J5 | 5 | J13 |
   | 2 | J4 | 6 | J10 |
   | 3 | J3 | 7 | J11 |

2. Confirm the 5-pin sensor pinout end-to-end before powering
   (**+3.3 V, +1.8 V, SCL, SDA, GND** — see
   [Hardware → Sensor connector](01-hardware.md#tof-sensor-connector-8)). A swapped
   power pin can damage the VL53L8CX.

## 2. Flash the firmware

```bash
cd ascend-tof8
make            # build (UART output)
make flash      # ST-Link + OpenOCD
```

> ⚠️ **Power-cycle the board after flashing.** The sensors hold the I²C bus after
> a debug reset and there are no XSHUT/NRST lines to release them — only a full
> power cycle clears the bus.

Optional live debug over ST-Link semihosting: `make run` (Ctrl-C to stop).

## 3. Bench-verify over UART

1. Connect the USB-UART adapter to `J7` (TX/RX/GND), host set to **921 600-8N1**.
2. Power the board (USB-C or `J1`).
3. Run the reader:
   ```bash
   python3 ascend-tof8/test/read_tof.py /dev/ttyUSB0
   ```
4. You should see the banner, a channel scan listing each detected sensor, the
   `N/8 sensors active` line, then repeating `--- CHn ---` grids of 8×8 mm values.
   Cold boot is **≈1.7 s per detected sensor** (firmware download dominates).

**Sanity checks**
- Wave your hand ~30 cm in front of one sensor → that channel's grid should drop
  to ~300 mm values. `0` = no return / invalid, not "obstacle at 0".
- If you see `ERROR: TCA9548A mux not responding!` → power-cycle; if it persists,
  check the mux RESET pull-up (must be to **3.3 V**) and I²C wiring.
- Missing a channel in the scan → check that sensor's cable/connector and that its
  NCS pulldown selects I²C mode.

## 4. Integrate with VOXL2

1. **Wire** the board's `J7` UART to a VOXL2 high-speed UART (e.g. `/dev/ttyHS1`)
   and power the board.
2. **Install** the companion:
   ```bash
   # build in voxl-cross, then on the VOXL2:
   dpkg -i voxl-ascend-8tof_<ver>_arm64.deb
   systemctl enable --now voxl-ascend-8tof
   ```
3. **Configure** `/etc/modalai/voxl-ascend-8tof.conf` — confirm `uart_path`
   matches the port you wired and `uart_baud = 921600`. (Defaults are otherwise
   good; see [VOXL integration → Configuration](05-voxl-integration.md#configuration-etcmodalaivoxl-ascend-8tofconf).)
4. **Verify pipes**:
   ```bash
   systemctl stop voxl-ascend-8tof
   voxl-ascend-8tof -d          # per-channel parse/publish stats
   voxl-inspect-pipes           # should list tof8_ch0..7
   ```
5. **Wire into voxl-mapper** — add the `tof_pipe_*` / `depth_pipe_*` slots and
   matching `extrinsics.conf` entries from
   [VOXL integration](05-voxl-integration.md#voxl-mapper-wiring). Mount the board
   with **CH3 facing the nose** to match the provided extrinsics table.
6. **Validate placement** — with voxl-mapper running, block one sensor at a time
   and confirm the obstacle shows up in the expected body direction in
   voxl-portal. Adjust that channel's RPY if it lands in the wrong direction.

## Troubleshooting quick-reference

| Symptom | Likely cause / fix |
|---------|--------------------|
| `TCA9548A mux not responding` | Power-cycle. Mux RESET pull-up must be 3.3 V, not 1.8 V. |
| A channel never `detected` | Bad cable/connector; NCS pulldown missing (I²C mode); sensor damaged. |
| Garbage / no UART text | Host baud wrong — use **921 600**, not 115 200 (banner text is stale). |
| Bus hangs after re-flash | Didn't power-cycle. Firmware also bit-bangs recovery, but power-cycle is the fix. |
| `invalid metadata, magic number=…` in voxl-mapper | `chN_format` doesn't match the slot type (tof2→tof_pipe, point_cloud→depth_pipe). |
| Obstacle appears in wrong direction | Wrong `RPY_parent_to_child` for that channel, or board not mounted CH3-forward. |
| Rear/side sensors ignored | Using the old single-merged-cloud config — upgrade to per-pipe (v0.1.0). |
