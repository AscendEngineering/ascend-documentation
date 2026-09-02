# Firmware

One codebase, built for a board variant and an avoidance output. Source:
[`AscendEngineering/ascend-8tof`](https://github.com/AscendEngineering/ascend-8tof).

```bash
make BOARD=horiz3 AVOID=cp          # v2, PX4 CollisionPrevention (default)
./tools/flash-board.sh              # flash over SWD and report which sensors came up
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

`EXCLUDE=` is how you keep a board flying with a known-bad sensor: the excluded
channel is never selected, so one failed part cannot take the other seven down
with it. See
[Bring-up → A sensor that jams the bus](06-bringup-setup.md#a-sensor-that-jams-the-bus).

Each combination builds into its own directory (`build/horiz3-cp`,
`build/horiz3-cp-ex4`, …) so a diagnostic image is never mistaken for a flight
image.

## Flashing

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

## What the firmware does

- Reads all 8 sensors through the mux at **15 Hz** each.
- Applies the persistent **zone mask** before anything downstream sees the cloud.
- Emits MAVLink per the `AVOID=` variant, and the raw cloud when a host asks.
- **Self-heals:** if every sensor fails bring-up it retries every ~2 s (the 5 V
  rail can sag during the 8-sensor inrush and fail a first attempt); a single
  channel that drops at runtime is retried round-robin, up to 5 attempts, and is
  skipped while avoidance is actively manoeuvring.

## Persistent zone mask

Zones can be permanently excluded — propellers, landing gear, the vehicle's own
frame. The mask is painted in the [configurator](https://tools.ascendengineer.com)
and saved to flash with `SAVE_MASK`.

It is stored in the **last two 8 KB sectors of bank 2** as alternating A/B slots
with a CRC and a sequence number, so an interrupted write can never destroy the
config currently in use. Firmware loads it before the first frame is served.
