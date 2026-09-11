# Install firmware

Install a prebuilt image on the **horizontal v3 STM32H563RGT6 carrier with
eight v2 VL53L8CX sensor boards**. This is the carrier used in the Ascend-8tof v2
system described here. The installer programs the sensor board, not the flight
controller. No firmware compiler or source checkout is required.

## Download

| Package | Profile | Status |
|---------|---------|--------|
| [Firmware and installer ZIP](downloads/firmware/2026.09.11-10hz10ms-uart10/ascend-8tof-horizontal-v3-2026.09.11-uart10.zip) | **8×8 · 10 Hz · 10 ms**, 10 Hz UART cloud, `AVOID=cp`, 180° orientation | **Bench installation verified on two boards** |
| [ZIP SHA-256 checksum](downloads/firmware/2026.09.11-10hz10ms-uart10/ascend-8tof-horizontal-v3-2026.09.11-uart10.zip.sha256) | Verify the complete download | Version `2026.09.11-10hz10ms-uart10` |

Read the [release notes and validation status](09-firmware-release-notes.md)
before installing. The ZIP contains the firmware, Python installer, launchers,
OpenOCD configuration, manifest, checksums, and offline instructions. Extract
**all files** into one folder; do not run the installer directly from the ZIP.

!!! note "Validation status"
    Firmware compilation, regression tests, and 15 installer tests passed.
    Installation, all-eight-sensor configuration/startup, firmware readback,
    and saved-mask preservation passed on two boards using macOS and ST OpenOCD.
    A 30-second UART capture on one board measured **9.98 cloud packets/s**.
    Range, input power, and Windows/Linux hardware installation remain unverified.

## Prerequisites

- [Python 3.9 or newer](https://www.python.org/downloads/).
- An **ST-Link** programmer with its USB drivers or Linux USB permissions
  configured. An FTDI UART cable displays sensor data; it does not flash this
  board.
- **ST OpenOCD with STM32H5 support**, including `interface/stlink-dap.cfg` and
  `target/stm32h5x.cfg`. Use the executable and scripts from the same ST
  distribution. ST OpenOCD is available with
  [STM32CubeIDE](https://www.st.com/en/development-tools/stm32cubeide.html)
  or from [ST's source](https://github.com/STMicroelectronics/OpenOCD).
  Generic OpenOCD 0.12 packages may lack STM32H5 support.
- The complete extracted release ZIP. Python, OpenOCD, and USB drivers are
  installed separately; the installer does not download them automatically.

The installer targets Windows, macOS, and Linux using Python's standard
library. The ST OpenOCD build used for earlier board flashing was
`0.12.0+dev-00635-g0a084c293`.

## Connect the board

Work on the bench with the vehicle disarmed and propellers removed. Supply
**regulated 5 V through J5 pin 1**, with ground on pin 4. See
[Power](02-power.md) and the [connector photos](01-hardware.md#connectors-pinouts).

Connect the ST-Link to J6:

| J6 pin | Board signal | ST-Link signal |
|--------|--------------|----------------|
| 1 | GND | GND |
| 3 | SWDIO | SWDIO |
| 4 | SWCLK | SWCLK |
| 6 | +3V3 | Target-voltage sense / VTref |

J6 pin 6 is a **voltage reference**, not an input for a programmer's power
output. Check the pinout of your particular ST-Link. SWO and RESET are not
required by this installer; it uses a software reset. Connect only one ST-Link,
or select a probe with `--serial`. Close other debugger/programmer sessions.

## Run the installer

Open a terminal in the extracted folder and check package integrity first:

=== "macOS / Linux"

    ```sh
    python3 install.py --check
    sh install.sh
    ```

=== "Windows"

    ```bat
    py -3 install.py --check
    .\install.cmd
    ```

If OpenOCD is not found, pass its paths explicitly. Replace the example paths
with the executable and scripts in your ST installation:

=== "macOS / Linux"

    ```sh
    python3 install.py --board horizontal-v3 \
      --openocd "/path/to/tools/bin/openocd" \
      --scripts "/path/to/scripts"
    ```

=== "Windows"

    ```bat
    py -3 install.py --board horizontal-v3 --openocd "C:\path\to\openocd.exe" --scripts "C:\path\to\scripts"
    ```

STM32CubeIDE may put scripts in the debug plugin's
`resources/openocd/st_scripts` folder, separate from the executable in the
external-tools OpenOCD plugin. `OPENOCD` and `OPENOCD_SCRIPTS` environment
variables can supply the same paths.

The installer checks the image, identifies the MCU and flash layout, and shows
the unique board ID. Confirm that the physical board is the **horizontal v3**:
a matching MCU cannot identify a PCB revision. Type **`INSTALL`** to continue.
Automated bench runs can add `--yes`.

The installer then:

1. Saves a complete **1 MiB flash backup** in a new local directory.
2. Programs and verifies the firmware region.
3. Resets the board and waits for startup.
4. Checks all eight sensors for autonomous mode, 8×8 resolution, 10 Hz, and 10 ms.
5. Checks that saved mask bytes are unchanged and verifies the installed image's
   SHA-256 checksum by reading it back.

Success requires all eight sensors to start with the expected settings. Backups,
logs, and `result.json` are stored under **`Ascend8TOF/backups` in your home
folder**. Use `--backup-dir PATH` to choose another location. Keep these files
with that board; they are not part of the public download.

## Verify the output

Open the [configurator](https://tools.ascendengineer.com) in Chrome, connect the
FTDI adapter at **921600 baud**, and check all eight channels. Move an object
in front of each sensor. The tip of the A marks the nose: **CH7/J8**.

With this release, the dashboard should show approximately **10 Hz**. Each UART
packet combines newly received channel readings from the MCU's faster 20 Hz
polling loop. `sensor_valid` identifies channels with new data in that packet;
it is separate from the online bitmap in `INFO`. The original 2026-09-10 image
sent approximately 20 packets/s while its sensors still ranged at 10 Hz.
Packet arrivals can have timing jitter, and not every packet must update every
channel. See [the measured results](09-firmware-release-notes.md#validation-status).

This release reports **unknown** for weak, missing, masked, expired, or
unmeasured directions. PX4 may restrict motion into those directions. Do not
set `CP_GO_NO_DATA` merely to hide missing measurements. Valid close obstacles
are retained; use deliberate zone masks for enclosure and airframe returns.
See [Communications](03-comms-protocol.md#obstacle_distance-field-values).

## Troubleshooting and rollback

| Problem | Next step |
|---------|-----------|
| OpenOCD or scripts not found | Supply the explicit paths above; confirm `stm32h5x.cfg` and `stlink-dap.cfg` exist. |
| No ST-Link or target | Check USB enumeration, board power, VTref, ground, cable orientation, drivers/permissions, and other debugger sessions. |
| Unexpected MCU, flash layout, or protection | Stop and check the board. The installer does not unlock devices, change option bytes, or perform a mass erase. |
| Sensor verification failed | Read `verify-sensors.log`. Programming may have succeeded while a sensor was disconnected; check all eight boards and their power, then retry. |
| Saved mask or image readback mismatch | Keep the full backup and logs; do not treat the installation as verified. |

For rollback, retain that board's `before-flash.bin` and logs. A full restore
also restores its original mask. Use an STM32H563-capable programmer to write
the backup at `0x08000000`, verify, and reset. Do not use another board's backup
or erase option bytes. The supplied installer accepts only its checksummed
release image.

Bench installation checks do not establish outdoor range, braking distance,
or readiness for flight. Configure and validate the flight controller separately
using the [integration guide](05-integration.md).
