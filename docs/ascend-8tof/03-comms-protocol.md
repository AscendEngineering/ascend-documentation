# Communications — UART Protocols

`J5` is v2's only host connector, and it carries **two protocols at once** at
**921 600 baud, 8N1**:

| Protocol | Direction | When it runs |
|----------|-----------|--------------|
| **MAVLink v2** | board → host (and host → board) | **always, unconditionally** |
| **Point-cloud link** (`0xA5 0x5A` framed) | board → host, on request | **only while a host asks for it** |

!!! warning "v1's ASCII stream is gone"
    v1 emitted plain-text `--- CH<n> ---` blocks followed by rows of integers.
    **v2 does not emit ASCII at all.** Both v2 protocols are binary and
    CRC-checked. Any v1 parser will need rewriting.

## Why a passive listener sees only MAVLink

This is the single most common surprise on v2, and it is deliberate.

`J5` is the board's only UART, so it has to serve both the flight controller and
the configurator. Rather than a mode switch — which could leave a vehicle flying
with avoidance disabled if it ever got stuck — **MAVLink always runs**, and only
the high-rate point cloud is gated:

- Any valid point-cloud command received from a host **arms** streaming and
  refreshes a deadline (`UART_LINK_GATE_MS`, 3 s).
- When the host stops talking, the deadline lapses and the cloud stops on its own.
- **At boot the gate is shut.**

So on the bench with a configurator attached you get the full cloud, and in
flight with nothing attached the link carries only MAVLink. Avoidance is never
suspended either way.

**The practical consequence:** you cannot sniff the point cloud. You have to ask
for it and keep asking, roughly once a second. If you are seeing MAVLink and no
`0xA5 0x5A` frames, that is the gate, not a fault.

Receive needs no gating — the USART2 interrupt mirrors every incoming byte to
both parsers, and each ignores what it does not recognise (MAVLink syncs on
`0xFD`, the point-cloud link on `0xA5 0x5A`, and both are CRC-checked).

## MAVLink output

What the board emits depends on the firmware variant (see
[Firmware](04-firmware.md)):

| Message | ID | Rate | Variant |
|---------|-----|------|---------|
| `HEARTBEAT` | 0 | 1 Hz | all |
| `OBSTACLE_DISTANCE` | **330** | **10 Hz** | `AVOID=cp` (default) |
| `SET_POSITION_TARGET_LOCAL_NED` | 84 | — | `AVOID=vfh` |

The board also *parses* `ODOMETRY` (331) and `ATTITUDE_QUATERNION` (31) coming
back from the flight controller, and uses the attitude for tilt compensation.

### `OBSTACLE_DISTANCE` field values

These are what PX4's collision prevention consumes; the values are chosen to
satisfy its gates exactly.

| Field | Value |
|-------|-------|
| `frame` | `MAV_FRAME_BODY_FRD` (12) |
| `sensor_type` | `MAV_DISTANCE_SENSOR_UNKNOWN` |
| `increment_f` | **5.0°** |
| `angle_offset` | **2.5°** (bin centres, not edges) |
| `distances[]` | **72 bins**, centimetres |
| `min_distance` | **50 cm** |
| `max_distance` | **400 cm** |

Two sentinel values matter:

- **`401` (`max_distance + 1`)** — bin is covered by a sensor and is **clear**.
- **`65535` (`UINT16_MAX`)** — bin is **not covered** (sensor offline, masked, or
  outside any field of view). PX4 treats unknown as blocking unless `CP_GO_NO_DATA`
  is set.

A bin is only reported clear if a live, unmasked sensor column actually covers
it. That distinction is what stops a dead sensor from being read as open space.

## Point-cloud link

The binary protocol the browser configurator speaks, carrying the **raw,
unmasked** 512-zone cloud plus the read/write path for the persistent zone mask.

### Framing

```
0xA5 0x5A  <type:u8>  <len:u16 LE>  <payload[len]>  <crc16:u16 LE>
```

CRC-16/MCRF4XX ("X.25") over `type + len + payload`. The two-byte sync word plus
the CRC lets a host that connects mid-stream resynchronise unambiguously, and
lets it skip the interleaved MAVLink bytes.

### Message types

| Direction | ID | Name | Payload |
|-----------|-----|------|---------|
| board → host | `0x01` | `INFO` | geometry: sensor count, grid size, per-channel bearings, mask sequence |
| board → host | `0x02` | `FRAME` | the full 512-zone cloud (below) |
| board → host | `0x03` | `MASK` | current 512-byte zone mask |
| board → host | `0x04` | `ACK` | reply to a host command |
| board → host | `0x05` | `DIAG` | why bring-up failed, per channel |
| host → board | `0x81` | `GET_INFO` | — |
| host → board | `0x82` | `GET_MASK` | — |
| host → board | `0x83` | `SET_MASK` | 512 gate bytes (RAM only) |
| host → board | `0x84` | `SAVE_MASK` | persist RAM mask to flash |
| host → board | `0x85` | `STREAM` | `u8` enable |
| host → board | `0x86` | `GET_DIAG` | — |

Any of the host → board messages re-arms the 3 s gate, so `GET_INFO` doubles as
a keepalive.

### `FRAME` payload

1554 bytes: an 18-byte header followed by eight fixed-size sensor blocks.

| Offset | Size | Field |
|--------|------|-------|
| 0 | u32 | `seq` |
| 4 | u32 | `timestamp_ms` |
| 8 | u8 | `sensor_valid` — bit *n* = channel *n* has data this frame |
| 9 | u8 | `odom_valid` |
| 10 | i16 | `roll_cdeg` |
| 12 | i16 | `pitch_cdeg` |
| 14 | i16 | `yaw_cdeg` |
| 16 | u16 | reserved |
| 18 | 8 × 192 | per-sensor block |

Each sensor block is **64 little-endian u16 ranges in mm**, then **64 status
bytes**. Channels with no data are sent as zeroes so the payload stays
fixed-size and a host can index it without parsing.

!!! note "Only status 5 and 9 are real measurements"
    Every other status is a no-return. Treat those zones as **no data** — never
    as "obstacle at 0 mm". `FRAME` deliberately carries the *unmasked* cloud so
    the configurator can show you what a mask would discard; everything
    downstream of this link (the planner, the MAVLink output) sees the masked
    cloud.

## Reading it

The supported tools live in the firmware repo:

```bash
# stream the raw 8×(8×8) matrices — handles the keepalive for you
python3 tools/tof8-stream.py                        # live grids
python3 tools/tof8-stream.py --format jsonl         # one JSON object per frame
python3 tools/tof8-stream.py --format csv -o cloud.csv

# link health / which channels are ranging
python3 tools/tof8-poll.py
```

Both are standard-library only (no `pyserial`) and run on Python 3.6, so they
work on a stock VOXL2 image.

!!! warning "One process owns the port"
    A serial port has one owner. If the configurator tab, `screen`, or
    `mavlink-router` holds `J5`, these tools cannot. On a VOXL2, `/dev/ttyHS1` is
    already owned by PX4's `mavlink` instance — two readers on one tty do not each
    get a copy, they race and both get a corrupted subset. `tof8-stream.py` warns
    when another process already holds the device.

## Graphical configurator

<https://tools.ascendengineer.com> — a browser tool (Chrome, via Web Serial) that
draws the live cloud in 3D and lets you paint and save the zone mask. It speaks
exactly the protocol above and keeps the gate open with a ~1 Hz keepalive.

Web Serial requires a **secure context**, so the tool must be loaded over HTTPS.
