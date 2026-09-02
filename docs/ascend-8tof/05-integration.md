# Integration

With the default `AVOID=cp` firmware, v2 speaks **stock MAVLink** to a stock
PX4. There is no plugin to install and no custom autopilot build: the board
emits `OBSTACLE_DISTANCE` (#330) and PX4's built-in collision prevention does
the avoiding.

!!! info "This replaced the v1 integration path"
    v1 exposed an ASCII stream consumed by the `voxl-ascend-8tof` plugin feeding
    voxl-mapper. **v2 emits no ASCII**, so that plugin does not apply. If you
    want the raw cloud on a host, read it with the binary protocol — see
    [Communications](03-comms-protocol.md).

## Wiring

| Board | Host |
|-------|------|
| `J5` pin 3 (TX) | host RX |
| `J5` pin 2 (RX) | host TX |
| `J5` pin 4 (GND) | host GND |
| `J5` pin 1 | regulated **5 V** |

Both data directions must be connected. The board needs attitude back from the
flight controller for tilt compensation, and the point-cloud link is gated on
hearing from a host at all.

## PX4 collision prevention

### 1. Give PX4 a MAVLink instance on that port

The board sends #330 at 10 Hz and needs `ODOMETRY` back. On a VOXL2, add this to
`/usr/bin/voxl-px4-start` **before** `mavlink boot_complete`:

```bash
# 8TOF obstacle array on /dev/ttyHS1. Sends OBSTACLE_DISTANCE (#330) for PX4
# collision prevention, and needs attitude back for tilt compensation.
# -m minimal, not onboard: the board only parses ODOMETRY (#331) and
# ATTITUDE_QUATERNION (#31), so a full onboard stream set is wasted bandwidth.
mavlink start -d /dev/ttyHS1 -b 921600 -m minimal -r 2000
mavlink stream -d /dev/ttyHS1 -s ODOMETRY -r 30
```

On other autopilots, point any spare TELEM port at the board at **921 600** and
make sure `ODOMETRY` is streamed back.

### 2. Set the parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `CP_DIST` | **> 0** (e.g. `1.5`) | Gates collision prevention entirely. At `-1` it is off and nothing else matters. |
| `MPC_POS_MODE` | **see below** | Determines whether the active flight task even *has* collision prevention. |
| `CP_GO_NO_DATA` | `0` (default) | Whether to allow movement into bins with no data. |

!!! danger "`MPC_POS_MODE` depends on your PX4 version"
    Collision prevention lives in a different flight task depending on release,
    and setting the wrong one produces a vehicle that flies happily through
    obstacles with no error message:

    | PX4 | Where CP lives | Working `MPC_POS_MODE` |
    |-----|----------------|------------------------|
    | **1.14** | `FlightTaskManualPosition` (and `…SmoothVel`) | **3** |
    | **1.18** | `StickAccelerationXY` | **4** |

    On 1.14, `MPC_POS_MODE=4` selects `FlightTaskManualAcceleration`, whose
    `StickAccelerationXY` has **no** collision prevention at all. Check the
    firmware version on the vehicle before trusting any guide — including this
    one.

Collision prevention is **position-mode only**. It does not act in altitude or
manual mode, and mission avoidance is a separate feature.

### 3. Verify PX4 is receiving it

```bash
listener obstacle_distance
```

You want a recent timestamp and a populated `distances` array. `never published`
means the messages are not arriving — check baud, wiring direction, and that the
`mavlink` instance is actually running on that device.

On a VOXL2 note the split architecture: `mavlink` runs on the **apps processor**
while `commander`, `flight_mode_manager` and `mc_pos_control` run on the **SLPI
DSP**. The topic crosses a `muorb` bridge, so check the subscriber count on the
DSP side too — a topic published on apps with zero DSP subscribers will look
alive and still do nothing.

### What "clear" and "unknown" mean

The board fills all 72 bins every message:

- **`401` cm** — covered by a live, unmasked sensor and **clear**.
- **`65535`** — **not covered**: sensor offline, zone masked, or outside every
  field of view. PX4 treats unknown as blocking unless `CP_GO_NO_DATA` is set.

A bin is only marked clear when a sensor column actually covers it, so a failed
sensor reads as *unknown* rather than *open space*. Expect a board with a dead
channel to restrict motion in that direction — that is the intended behaviour.

## Reading the raw cloud on a host

If you want the 512-zone cloud rather than (or as well as) avoidance:

```bash
python3 tools/tof8-stream.py --format jsonl     # one JSON object per frame
python3 tools/tof8-stream.py --format csv -o cloud.csv
```

Standard library only, Python 3.6+, so it runs on a stock VOXL2 image. See
[Communications](03-comms-protocol.md#point-cloud-link) for the wire format if
you are writing your own parser.

!!! warning "You cannot share the port with PX4"
    A tty has one owner. If PX4's `mavlink` holds `/dev/ttyHS1`, a second reader
    does not get a copy — they race, and both get a corrupted subset. Stop the
    `mavlink` instance on that device first, or read the board from a separate
    machine over a USB-UART adapter.

## Geometry, if you are building your own consumer

For an 8×8 grid with per-axis FoV `fov_deg` (45°), in the sensor's optical frame
(x-right, y-down, z-forward):

```
step  = (fov_deg / 8) * π/180          # angular pitch between zones
ax    = (col - 3.5) * step             # azimuth off optical axis
ay    = (row - 3.5) * step             # elevation off optical axis
dir   = normalize( tan(ax), tan(ay), 1 )
point = (distance_mm / 1000) * dir     # metres, sensor optical frame
```

Then rotate by that channel's mounting bearing from
[Hardware](01-hardware.md#sensor-connectors-8-100-mm-5-pin) to reach the body
frame. The board ships those bearings in its `INFO` message, so a host can read
them rather than hard-coding a second copy.

## Validating placement before flight

With the vehicle disarmed, block one sensor at a time and confirm the obstacle
appears in the expected body direction — in the
[configurator](https://tools.ascendengineer.com), or via `listener
obstacle_distance` by checking which bins drop.

The single most common integration error is mounting rotation. On v2 the nose is
**CH7 (`J8`)**, under the tip of the "A".
