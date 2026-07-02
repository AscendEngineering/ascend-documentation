# Bring-up & Setup Guide

End-to-end procedure to go from boards in a box to a working obstacle sensor on
your host. The board ships **pre-flashed by Ascend** with your chosen
[firmware variant](04-firmware.md) — there's nothing to build or flash.

## 0. What you need

- Ascend main board + up to 8 TOF sub-boards.
- 8× 5-pin sensor cables (main-board sensor ports → TOF sub-boards).
- A **regulated 5 V supply** on `J1`, **or** a USB-C cable
  (see [Power](02-power.md)).
- A USB-UART adapter (921 600-capable) for the bench check, wired to `J7`
  — *default (sensor-stream) firmware only*.
- For flight integration: **any host with a UART** (flight controller or onboard
  computer). This guide uses a VOXL2 as the worked example; see
  [Integration (any host)](05-integration.md) for other platforms.

## 1. Assemble & connect

1. Plug each TOF sub-board into a main-board sensor port with a 5-pin cable. Note
   the **channel ↔ port map** — it determines each sensor's bearing in software:

   | Channel | Port | Channel | Port |
   |---------|------|---------|------|
   | 0 | J6 | 4 | J12 |
   | 1 | J5 | 5 | J13 |
   | 2 | J4 | 6 | J10 |
   | 3 | J3 | 7 | J11 |

2. Seat every cable fully before powering — see the connector pinouts in
   [Hardware](01-hardware.md#sensor-connector-8-5-pin).

## 2. Power & bench-verify

*(Default sensor-stream firmware — skip to step 3 if your board runs the ACO
firmware, which talks to a flight controller rather than a terminal.)*

1. Connect the USB-UART adapter to `J7` (board **TX → adapter RX**, GND↔GND), host
   set to **921 600-8N1**.
2. Power the board (5 V on `J1`, or USB-C).
3. Open the port in any serial terminal:
   ```bash
   screen /dev/tty.usbserial-XXXX 921600     # or minicom -D /dev/ttyUSB0 -b 921600
   ```
4. You should see repeating `--- CHn ---` blocks, each followed by an **8×8 grid**
   of millimetre distances — one per connected sensor, updating continuously.

**Sanity checks**
- Wave your hand ~30 cm in front of one sensor → that channel's grid should drop
  to ~300 mm values. `0` = no return / invalid, **not** "obstacle at 0".
- A missing channel → check that sensor's cable and connector seating.

## 3. Integrate with your host

Any host that can read the UART works. For a generic recipe (ArduPilot / PX4, ROS,
bare MCU, …) see [Integration (any host)](05-integration.md). The steps below are
the **VOXL2 worked example** (default firmware).

1. **Wire** the board's `J7` UART to a VOXL2 high-speed UART (e.g. `/dev/ttyHS1`)
   and power the board.
2. **Install** the Ascend-provided service:
   ```bash
   dpkg -i voxl-ascend-8tof_<ver>_arm64.deb
   systemctl enable --now voxl-ascend-8tof
   ```
3. **Configure** `/etc/modalai/voxl-ascend-8tof.conf` — confirm `uart_path`
   matches the port you wired and `uart_baud = 921600` (see
   [Integration → Configuration](05-integration.md#configuration-etcmodalaivoxl-ascend-8tofconf)).
4. **Wire into voxl-mapper** — add the `tof_pipe_*` / `depth_pipe_*` slots and
   matching `extrinsics.conf` entries from
   [Integration](05-integration.md#voxl-mapper-wiring). Mount the board with
   **CH3 facing the nose** to match the extrinsics table.
5. **Validate placement** — with voxl-mapper running, block one sensor at a time
   and confirm the obstacle shows up in the expected body direction in
   voxl-portal. Adjust that channel's mounting rotation if it lands wrong.

> **ACO firmware:** instead of the above, wire `J7` to a flight-controller TELEM
> port and enable the autopilot's obstacle-avoidance feature — see
> [ACO Firmware](04-firmware.md#aco-firmware-onboard-collision-avoidance-beta).

## Troubleshooting quick-reference

| Symptom | Likely cause / fix |
|---------|--------------------|
| No UART text at all | Wrong baud — use **921 600-8N1**; confirm board TX → adapter RX (not TX→TX). |
| Garbled text | Baud mismatch — set 921 600. |
| A channel never appears | Bad/loose sensor cable or connector. |
| `invalid metadata, magic number=…` in voxl-mapper | `chN_format` doesn't match the slot type (tof2 → tof_pipe, point_cloud → depth_pipe). |
| Obstacle appears in wrong direction | Wrong per-channel mounting rotation, or board not mounted CH3-forward. |
| Rear/side sensors ignored | Using an old single-merged-cloud config — use per-pipe publishing. |
