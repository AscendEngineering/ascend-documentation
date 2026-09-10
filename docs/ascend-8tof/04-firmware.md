# Firmware

## Prebuilt firmware and installer

The [2026.09.10-10hz10ms download](08-install-firmware.md) is a **bench candidate**
for the horizontal v3 carrier with eight v2 sensor boards. It uses 8×8 zones,
10 Hz per sensor, 10 ms sub-integration, `AVOID=cp`, and 180° zone orientation.
It also corrects weak/invalid readings being reported as clear space.

The package includes its installer and offline instructions. No source checkout
or compiler is needed. Read the [release notes](09-firmware-release-notes.md)
and [pending hardware-validation status](09-firmware-release-notes.md#validation-status)
before using it.

## Source builds

The firmware codebase is
[`AscendEngineering/ascend-8tof`](https://github.com/AscendEngineering/ascend-8tof).
Source builds select a board variant and an avoidance output. Use the versioned
package for the candidate above; a checkout of the firmware repository is not
proof that it contains every change in that prebuilt image.

```bash
make BOARD=horiz3 AVOID=cp          # source default profile; not the versioned candidate installer
```

## Board variant — `BOARD=`

Always build with **`BOARD=horiz3`** (`oa_pcb_STM32H5_horizontal`). It selects the
single-UART configuration: `J5` carries MAVLink *and* the gated point cloud.

!!! warning "`BOARD=` does not default to this board"
    The Makefile's default targets a different variant, so omitting `BOARD=horiz3`
    silently builds an image that will not work here. Pass it every time — or use
    `tools/flash-board.sh`, which sets it for you.

## Avoidance output — `AVOID=`

This selects what goes on the MAVLink wire. The point-cloud link is unaffected.

| Value | Emits | Who avoids | Requires |
|-------|-------|-----------|----------|
| **`cp`** (default) | `OBSTACLE_DISTANCE` (#330) at 10 Hz | **stock PX4** collision prevention | `CP_DIST > 0` on the FC |
| `vfh` | `SET_POSITION_TARGET_LOCAL_NED` (#84) | the **board**, running VFH+ | the Ascend PX4 fork |
| `both` | both | — | bench comparison only |

!!! warning "`AVOID=both` is not a flight configuration"
    On a fork that honours #84, the two controllers fight over the same axis.
    Use it to compare behaviour on the bench, never on a vehicle.

`AVOID=cp` is the one to use unless you are specifically working on the fork —
it needs no custom PX4. See
[Obstacle Avoidance](07-obstacle-avoidance.md) for the `vfh` path and
[Integration](05-integration.md) for the `cp` path.

## Diagnostic and repair builds

These exist for bring-up and board repair. They are not flight builds.

| Option | Purpose |
|--------|---------|
| `DIAG=1` | Cold-boot I²C bus walk — finds a sensor that jams the bus |
| `DIAG=1 DIAGDIR=down` | The same walk in descending channel order |
| `EXCLUDE=4` | Permanently skip mux channel 4 (comma-separate for several) |

`EXCLUDE=` can isolate a known-bad sensor during diagnosis: the excluded
channel is never selected, so one failed part cannot take the other seven down
with it. See
[Bring-up → A sensor that jams the bus](06-bringup-setup.md#a-sensor-that-jams-the-bus).

Each combination builds into its own directory (`build/horiz3-cp`,
`build/horiz3-cp-ex4`, …) so a diagnostic image is never mistaken for a flight
image.

## Flashing

For the downloadable candidate, follow [Install Firmware](08-install-firmware.md).
It checks package integrity, backs up flash, verifies the image and sensor
profile, and checks saved masks. The commands below are the firmware
repository's older source-build workflow, not the packaged installer.

v2 has no USB and no bootloader button — **firmware goes on over SWD** via `J6`
with an ST-Link.

```bash
AVOID=cp BOARD=horiz3 ./tools/flash-board.sh
```

The script identifies the chip, flashes, waits for bring-up and prints the
per-channel result:

```
firmware  : build/horiz3-cp/ascend-horiz3-fw.elf
board UID : 00520036
** Programming Finished **
** Verified OK **
uptime    : 12.6 s
sensors   : 8/8
result    : ALL 8 CHANNELS OK
```

!!! note "A reset is not a power cycle"
    The script's post-flash reading happens after a **reset**, which does not
    clear the TCA9548A's channel latch. A board whose bus was jammed before
    flashing will still report `0/8` afterwards even if it is fine. Power-cycle
    it and re-check with `./tools/read-sensors.sh`, which reads a running board
    without resetting it.

## Ranging and measurement behavior

- The sensors support up to **15 Hz** at 8×8; older builds use that rate. The
  downloadable candidate explicitly selects **10 Hz / 10 ms**.
- The persistent zone mask applies to avoidance processing. The browser receives
  the raw cloud so users can see and edit the returns being excluded.
- `AVOID=cp` sends `OBSTACLE_DISTANCE` at 10 Hz, independently of the sensor
  rate. A faster browser packet counter is not a faster sensor measurement rate.
- The candidate reports weak, missing, masked, expired, and unmeasured directions
  as **unknown**. It retains close valid obstacles instead of discarding all
  measurements below 50 cm, and expires cached samples after 200 ms.
- Initialization retries and per-channel recovery exist in the source. The
  candidate reapplies its selected profile during recovery; physical recovery
  fault injection remains unverified. A stuck I²C bus can still require a
  power cycle or hardware repair.

See [release notes](09-firmware-release-notes.md) for the exact changes and
validation limits. These descriptions do not imply every older board already
has the candidate installed.

## Persistent zone mask

Zones can be permanently excluded — propellers, landing gear, the vehicle's own
frame. The mask is painted in the [configurator](https://tools.ascendengineer.com)
and saved to flash with `SAVE_MASK`.

It is stored in the **last two 8 KB sectors of bank 2** as alternating A/B slots
with a CRC and a sequence number, so an interrupted write can never destroy the
config currently in use. Firmware loads it before the first frame is served.
