# Integration

The Ascend-8tof board's **entire interface to the outside world is a plain ASCII
distance stream over UART** (921600-8N1). It is **not tied to any specific
autopilot or onboard computer** — anything with a serial port can read it: a
flight controller (ArduPilot / PX4), a companion computer (Raspberry Pi, NVIDIA
Jetson, ModalAI VOXL2, …), or even a bare microcontroller.

This page covers the **host-agnostic integration first**, then documents the
**VOXL2 + voxl-mapper** path in detail as a *worked example* — that's simply the
platform we know best and ship a ready-made plugin (`voxl-ascend-8tof`) for. None
of the board or firmware is VOXL-specific.

> Whatever you build — obstacle avoidance, SLAM/mapping, logging, a proximity
> alarm — you consume the same stream documented in
> [Communications & Protocols](03-comms-protocol.md).

## The stream, in one paragraph

For each sensor with fresh data the firmware prints a header line `--- CH<n> ---`
then 8 rows of 8 integers — an 8×8 grid of distances in millimetres, with `0`
meaning no return / invalid. Each sensor updates at 15 Hz; channels are
interleaved as data becomes ready. See
[the exact wire format](03-comms-protocol.md#wire-format-ascii) for the bytes.

## Generic integration recipe (any host)

1. **Wire it up.** Board `J7` UART: TX (pin 3) → host RX, GND (pin 4) → host GND
   (host TX → board RX is optional; the protocol is one-way). Power the board from
   5 V — see [Power](02-power.md).
2. **Open the port** at **921600-8N1**, no flow control.
3. **Parse** line-by-line: on `--- CH<n> ---` begin a new grid for channel *n*;
   the next 8 lines each carry 8 integers → fill the 8×8 grid; treat `0` as
   "no return".
4. **Interpret geometry (optional).** If you need 3-D points rather than raw
   per-zone ranges, convert each zone to a direction with the field-of-view model
   below, then scale by the measured range. Which physical direction each channel
   faces is entirely your mounting choice (the VOXL2 example below shows the 8-way
   360° layout we use).
5. **Use it.** Feed the ranges/points into your obstacle-avoidance, mapping, or
   logging logic.

### Field-of-view model (per zone)

For an 8×8 grid with total per-axis FoV `fov_deg` (default 45°), in the sensor's
own optical frame (x-right, y-down, z-forward):

```
step   = (fov_deg / 8) * π/180                     # angular pitch between zones
ax     = (col - 3.5) * step                        # azimuth off optical axis
ay     = (row - 3.5) * step                        # elevation off optical axis
dir    = normalize( tan(ax), tan(ay), 1 )          # unit ray
point  = (distance_mm / 1000) * dir                # metres, sensor optical frame
```

Then apply your sensor→body mounting rotation to place each point in the vehicle
frame. (The VOXL2 example offloads this last step to voxl-mapper via
`extrinsics.conf`.)

### Notes for other hosts

- **ArduPilot / PX4:** two options. **(a)** Run the
  [**ACO firmware** (beta)](04-firmware.md#aco-firmware-onboard-collision-avoidance-beta)
  — the board itself speaks MAVLink v2 (`OBSTACLE_DISTANCE`) straight to a TELEM
  port, no companion computer and no ASCII parsing at all. **(b)** With the default
  firmware, run a small companion-computer script that reads the UART and
  republishes over MAVLink (`OBSTACLE_DISTANCE` / `DISTANCE_SENSOR`) or DDS/uORB.
  Either way the 8 channels map naturally onto `OBSTACLE_DISTANCE` sectors.
- **ROS / ROS 2:** parse the stream in a node and publish `LaserScan`,
  `PointCloud2`, or per-sensor `Range` messages.
- **Bare MCU:** read ranges directly for a reactive proximity/braking behavior —
  no point cloud required.

---

## Example: VOXL2 + voxl-mapper (`voxl-ascend-8tof`)

The rest of this page is the **worked example** for a ModalAI VOXL2, using our
`voxl-ascend-8tof` VOXL-SDK service. It reads the UART stream above, projects each
grid into 3-D points with the FoV model, and publishes **one MPA pipe per
channel** for **voxl-mapper** to consume as independent ToF cameras, each placed
by its mounting transform in `extrinsics.conf`.

```
                        /run/mpa/tof8_ch0 ┐
ascend-8tof ──UART──►  voxl-ascend-8tof ──┤ one packet per channel ├──► voxl-mapper
                        /run/mpa/tof8_ch7 ┘
```

- **Software:** `voxl-ascend-8tof`, an Ascend-provided VOXL-SDK service (systemd).
- **Target host:** VOXL2 / QRB5165.

### Why one pipe per channel (v0.1.0)

voxl-mapper's ToF ingestion **discards any point with z ≤ 0 before applying the
per-pipe extrinsic**. The old v0.0.x design merged all 8 sensors into one forward
cloud, so every sensor outside the forward hemisphere was culled — a 360° ring
was impossible. Publishing each channel on its own pipe, in its own +z-forward
optical frame, keeps every point valid and lets voxl-mapper do per-sensor
ray-casting for proper free-space carving.

### Data path

| Stage | Detail |
|-------|--------|
| **Input** | UART (default `/dev/ttyHS1`, **921600-8N1**). Board prints `--- CH<n> ---` then 8 rows of 8 mm distances (0 = invalid). |
| **Parse** | Header `--- CH<n>` sets the current channel; each subsequent row of 8 ints fills the 8×8 grid; grid timestamped on completion. |
| **Project** | Each zone → a ray from the [FoV model](#field-of-view-model-per-zone) at the measured range, in the sensor's own optical frame. Invalid (0 mm) and out-of-range (> `max_range_m`) zones dropped. |
| **Publish** | One packet per channel on `chN_pipe`, `confidences = 255`, rate-limited per channel to `output_rate_hz`. |
| **Place** | voxl-mapper looks up each pipe's extrinsic by name in `/etc/modalai/extrinsics.conf` and transforms the cloud into body frame. |

### Packet formats

voxl-mapper has two ingestion paths with different packet types; `chN_format`
selects which one a channel publishes:

| `chN_format` | Packet type | Magic | voxl-mapper slot | Size |
|-------------|-------------|-------|------------------|------|
| `tof2` | `tof2_data_t` (organized 8×8, ray-cast path) | `VOXM` | `tof_pipe_0..3` | ~777 KB/frame |
| `point_cloud` | `point_cloud_metadata_t` (unstructured) | `VOXL` | `depth_pipe_0..3` | ~40 B + 12 B/point |

> Route the wrong format to a slot and voxl-mapper logs
> `invalid metadata, magic number=…`. voxl-mapper has exactly **4 tof + 4 depth
> slots = 8**, so all 8 sensors fit if you split them 4/4 (this is the default).

### Install

Ascend provides the `voxl-ascend-8tof` service as a prebuilt package. Install it
on the VOXL2 and enable it:

```bash
dpkg -i voxl-ascend-8tof_<ver>_arm64.deb
systemctl enable --now voxl-ascend-8tof
```

Contact Ascend for the latest package build.

### Configuration — `/etc/modalai/voxl-ascend-8tof.conf`

Created with defaults on first run.

| Key | Default | Meaning |
|-----|---------|---------|
| `uart_path` | `/dev/ttyHS1` | serial device the board is on (VOXL2 HS UARTs are `/dev/ttyHS0..3`) |
| `uart_baud` | `921600` | must match firmware (see [comms](03-comms-protocol.md#baud-rate-important)) |
| `fov_deg` | `45.0` | total per-axis VL53L8CX FoV |
| `max_range_m` | `4.0` | drop zones farther than this (8×8 is reliable to ~4 m) |
| `output_rate_hz` | `15.0` | per-channel max publish rate |
| `grid_stale_ms` | `200` | drop a channel grid older than this |
| `chN_enable` | `true` (all 8) | include firmware channel N |
| `chN_pipe` | `/run/mpa/tof8_chN` | MPA pipe this channel publishes on |
| `chN_format` | `tof2` for CH2/3/4/7, `point_cloud` for CH0/1/5/6 | packet type; must match the voxl-mapper slot |

> The v0.0.x per-channel `chN_roll/pitch/yaw/x/y/z` keys and the global
> `output_pipe` key are **removed** — the mounting transform now lives in
> `extrinsics.conf`. Delete them from any pre-existing config (the service
> rewrites defaults on first run).

### voxl-mapper wiring

Wire each `chN_pipe` into a `tof_pipe_N` / `depth_pipe_N` slot in
`/etc/modalai/voxl-mapper.conf`, each with its own extrinsic name.
Recommended allocation (forward+sides on the better tof ray-casting path, rear on
depth):

```jsonc
"tof_pipe_0":   "/run/mpa/tof8_ch3", "tof_0_enable": true, "tof_0_rate": 15, "tof_extrinsics_0_name": "tof8_ch3",  // N
"tof_pipe_1":   "/run/mpa/tof8_ch4", "tof_1_enable": true, "tof_1_rate": 15, "tof_extrinsics_1_name": "tof8_ch4",  // NE
"tof_pipe_2":   "/run/mpa/tof8_ch2", "tof_2_enable": true, "tof_2_rate": 15, "tof_extrinsics_2_name": "tof8_ch2",  // NW
"tof_pipe_3":   "/run/mpa/tof8_ch7", "tof_3_enable": true, "tof_3_rate": 15, "tof_extrinsics_3_name": "tof8_ch7",  // E

"depth_pipe_0": "/run/mpa/tof8_ch6", "depth_pipe_0_enable": true, "depth0_rate": 15, "extrinsics0_name": "tof8_ch6",  // SE
"depth_pipe_1": "/run/mpa/tof8_ch5", "depth_pipe_1_enable": true, "depth1_rate": 15, "extrinsics1_name": "tof8_ch5",  // S
"depth_pipe_2": "/run/mpa/tof8_ch1", "depth_pipe_2_enable": true, "depth2_rate": 15, "extrinsics2_name": "tof8_ch1",  // SW
"depth_pipe_3": "/run/mpa/tof8_ch0", "depth_pipe_3_enable": true, "depth3_rate": 15, "extrinsics3_name": "tof8_ch0",  // W
```

### Extrinsics — `/etc/modalai/extrinsics.conf`

For a board mounted flat on top of the FCU with **CH3 facing the drone's nose**,
body frame FRD (X forward, Y right, Z down). Each sensor needs a `body`→`tof8_chN`
entry. **This bearing table is also the reference layout for the 8-way 360° ring
on any host** — the RPYs are just how we express it for voxl-mapper.

**Convention:** ModalAI's `RPY_parent_to_child` produces a matrix labeled
`R_child_to_parent` — column 2 is the sensor's optical Z (forward) expressed in
body coordinates (verify with `voxl-inspect-extrinsics -p body -c tof8_ch3`).

| CH | Bearing | `T_child_wrt_parent` | `RPY_parent_to_child` (intrinsic XYZ, deg) |
|----|---------|----------------------|--------------------------------------------|
| CH3 | N (forward) | `[0,0,0]` | `[0, 90, 90]` |
| CH4 | NE | `[0,0,0]` | `[-90, 45, 180]` |
| CH7 | E (right) | `[0,0,0]` | `[-90, 0, 180]` |
| CH6 | SE | `[0,0,0]` | `[-90, -45, 180]` |
| CH5 | S (rear) | `[0,0,0]` | `[90, -90, 0]` |
| CH1 | SW | `[0,0,0]` | `[90, -45, 0]` |
| CH0 | W (left) | `[0,0,0]` | `[90, 0, 0]` |
| CH2 | NW | `[0,0,0]` | `[90, 45, 0]` |

Translation can stay at zeros for first-pass mapping (sensors sit ~3 cm from FCU
center — negligible at meter scale). **Verify each channel empirically:** with
voxl-mapper running, block one sensor at a time and confirm the obstacle appears
in the expected body direction in voxl-portal.

### Debugging

```bash
systemctl stop voxl-ascend-8tof
voxl-ascend-8tof -d                         # parse/publish stats per channel
voxl-ascend-8tof -c                         # create/print config then exit
voxl-inspect-pipes                          # list all pipes and clients
voxl-inspect-tof    tof8_ch3                # tof2 channels (CH2/3/4/7)
voxl-inspect-points tof8_ch0                # point_cloud channels (CH0/1/5/6)
voxl-inspect-extrinsics -p body -c tof8_ch3 # verify resolved R_child_to_parent
```

### Version history (`voxl-ascend-8tof`)

- **v0.1.0** — one MPA pipe per channel (breaking); `chN_format` selectable
  (tof2/point_cloud); mounting transform moved to `extrinsics.conf`; all 8
  channels on by default; `max_range_m` 6→4, `grid_stale_ms` 500→200.
- **v0.0.1** — initial release; merged all channels into a single `tof2` cloud on
  `/run/mpa/tof`.
