# Firmware release notes

## 2026.09.10-10hz10ms — bench candidate

[Download and install](08-install-firmware.md) this candidate for the horizontal
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
vehicle motion. The raw browser protocol retains its original per-poll fresh
sensor bitmap.

!!! warning "Unknown directions can restrict movement"
    PX4 Collision Prevention may restrict movement into open sky or poorly
    measured directions. Do not enable `CP_GO_NO_DATA` merely to hide missing
    measurements. This release does not claim continuous calibrated coverage
    between individual zone rays or guaranteed 4 m visibility outdoors.

### Power and timing

Each complete 8×8 frame uses four sub-integrations. The candidate has a 100 ms
frame interval and 40 ms of exposure per frame: **40% calculated exposure duty**.
This is not total board power.

| Profile | Frame interval | Exposure per frame | Exposure duty |
|---------|---------------:|-------------------:|--------------:|
| Earlier 15 Hz / 5 ms experiment | 67 ms | 20 ms | 30% |
| **This candidate: 10 Hz / 10 ms** | **100 ms** | **40 ms** | **40%** |
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

**Pending:** an end-to-end hardware installation and all-eight-sensor readback
of this exact release. The installation attempt stopped during identification,
before backup or flash, because the ST-Link was absent from USB. Earlier 5 ms
flashes do not validate this candidate. Windows/Linux hardware installation,
power, range, optical calibration, and recovery fault injection remain
unverified.

The ZIP includes `VALIDATION.md`, offline installation instructions, the release
manifest, checksums, and third-party notices. It is a bench candidate, not a
flight-validation result.

References: [ST integration timing and target-status interpretation](https://www.st.com/content/st_com/en/technical-documents/UM3109.html),
[MAVLink distance and unknown values](https://mavlink.io/en/messages/common.html#OBSTACLE_DISTANCE).
