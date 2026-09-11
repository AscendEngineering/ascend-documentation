# Firmware release notes

## 2026.09.11-10hz10ms-uart10 — bench installation verified

[Download and install](08-install-firmware.md) this release for the horizontal
v3 STM32H563RGT6 carrier with eight v2 VL53L8CX sensor boards.

| Setting | Value |
|---------|-------|
| Sensor grid | 8×8 per sensor; 512 zones total |
| Sensor rate | **10 Hz per sensor** |
| Sub-integration | **10 ms**, four per 8×8 frame |
| Ranging mode | Autonomous |
| Output | `AVOID=cp`: MAVLink `OBSTACLE_DISTANCE` at 10 Hz |
| Zone orientation | 180°, matching the fitted v2 sub-boards |
| Host UART | 921600 baud, 8N1 |
| Raw point-cloud packets | Approximately 10 Hz; 9.98 Hz measured |

### UART output update

The previous 2026-09-10 image sent a raw-cloud packet after every acquisition
poll, so the dashboard read about 20 Hz even though the sensors were configured
for 10 Hz. This update batches the latest newly received channel readings into
10 Hz UART packets. Acquisition continues polling at 20 Hz to collect staggered
sensor arrivals. Sensor integration and MAVLink collision-prevention timing
are unchanged.

Empty polls do not overwrite unsent channel readings. New invalid readings
replace old returns, already consumed readings are not repeated as fresh,
and delayed samples expire. Missed output deadlines do not cause catch-up
bursts. The existing binary protocol and browser connection remain compatible.
The batch timestamp and attitude come from its latest acquisition poll;
the eight sensors do not expose simultaneously.

The installer also fixes a pre-flash compatibility issue: it now explicitly
prints OpenOCD's flash-bank result before checking the memory layout. Device
checks, backups, saved masks, option bytes, and programming addresses retain
their existing behavior.

### Measurement handling

Weak, inconsistent, and no-target readings now leave their direction
**unknown**. A successful sensor read, an unmasked field of view, or a missing
echo no longer declares clearance to 4 m. Masked returns, excluded floor/ceiling
returns, out-of-range readings, and gaps between measured angular directions
also remain unknown.

Accepted status 5 or 9 measurements provide obstacle distances. Status 9 can
represent a merged target; it is accepted as an obstacle, not as proof of
clearance. Target-count output is enabled so a zone without a target is marked
as no data rather than trusting a leftover distance/status.

**Close obstacles below 50 cm are retained.** The advertised minimum is 2 cm;
a positive reading below that is reported at the minimum rather than discarded.
Use deliberate zone masks for enclosure and airframe returns.

The avoidance path keeps each sensor's latest frame between polls and expires
it **200 ms after its successful polling pass**, including when acquisition
stalls. New invalid readings replace old valid readings immediately. These
host timestamps do not compensate for exposure time, transport delay, or
vehicle motion. The raw UART protocol identifies channels with newly collected readings
in each output batch using its existing fresh-sensor bitmap.

!!! warning "Unknown directions can restrict movement"
    PX4 Collision Prevention may restrict movement into open sky or poorly
    measured directions. Do not enable `CP_GO_NO_DATA` merely to hide missing
    measurements. This release does not claim continuous calibrated coverage
    between individual zone rays or guaranteed 4 m visibility outdoors.

### Power and timing

Each complete 8×8 frame uses four sub-integrations. The release has a 100 ms
frame interval and 40 ms of exposure per frame: **40% calculated exposure duty**.
This is not total board power.

| Profile | Frame interval | Exposure per frame | Exposure duty |
|---------|---------------:|-------------------:|--------------:|
| Earlier 15 Hz / 5 ms experiment | 67 ms | 20 ms | 30% |
| **This release: 10 Hz / 10 ms** | **100 ms** | **40 ms** | **40%** |
| Earlier 15 Hz / 10 ms profile | 67 ms | 40 ms | 60% |

Longer exposure can improve weak-target detection, with less frequent updates
than 15 Hz / 5 ms. It does not automatically correct calibration errors.
Compare input watts, missed detections, and measurement age with the same
scene, supply, and peripherals. See [Power](02-power.md#choosing-a-ranging-profile).

### Installation and saved settings

Startup and sensor recovery use shared configuration/readback checks for mode,
rate, resolution, and integration. The packaged installer checks those values
on all eight sensors after programming. Saved zone masks keep their existing
layout and orientation, and the installer checks their bytes before/after.

### Validation status

**Passed:** ARM compilation/link; obstacle-status, close-range, mask, angular-gap,
freshness/expiry, and timer-wrap regressions; existing protocol and orientation
tests; 15 installer tests; package-integrity checks.

**Hardware passed on two boards:** complete 1 MiB backups, programming and
firmware readback checksums, all eight sensors started in autonomous 8×8 mode
at 10 Hz / 10 ms, and saved-mask bytes preserved. Both installations used
macOS with ST OpenOCD `0.12.0+dev-00635-g0a084c293`.

**UART measured on one board:** 19.30 packets/s before the update in a 12-second
capture; **9.98 packets/s after the update** in a 30-second capture, receiving
299 CRC-valid cloud packets with no sequence gaps and all eight channels online.
Individual arrival intervals varied from 31 to 167 ms. The 10 Hz rate is an
average cadence, not a guarantee of perfectly spaced packet arrivals.
Fresh-channel delivery measured 8.91–9.95 updates/s across the channels; not
every packet necessarily contains a new reading from every channel.

Stream regressions also cover staggered channels, invalid replacement,
individual expiry, service-task jitter, skipped deadlines and timer wrap.

**Still unverified:** Windows/Linux hardware installation, input power, range,
optical calibration, sensor recovery fault injection, and flight performance.

The ZIP includes `VALIDATION.md`, offline installation instructions, the release
manifest, checksums, and third-party notices. It is a bench release, not a
flight-validation result.

References: [ST integration timing and target-status interpretation](https://www.st.com/content/st_com/en/technical-documents/UM3109.html),
[MAVLink distance and unknown values](https://mavlink.io/en/messages/common.html#OBSTACLE_DISTANCE).
