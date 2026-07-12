# Obstacle Avoidance — Onboard VFH + PX4 Setpoint Fusion

This page explains a third avoidance approach for the Ascend-8tof: the board runs
the avoidance planner **on-board**, computes the *best evasive motion itself*, and
**streams velocity setpoints** to a **PX4 flight controller** that has been
extended to accept and blend them during normal flight. The drone steers around
obstacles while a mission or the pilot stays in control.

!!! note "Where this sits vs. the other firmware"
    | Approach | Who decides the maneuver | Talks to FC as | Avoids in |
    |----------|--------------------------|----------------|-----------|
    | **Sensor stream** (default) | Your host | ASCII 8×8 grids | up to you |
    | **ACO** ([firmware](04-firmware.md)) | The board | `OBSTACLE_DISTANCE` → PX4 Collision Prevention (brake/deflect) | Position mode |
    | **Setpoint streaming** (this page) | The board (VFH) | `SET_POSITION_TARGET` → **forked PX4** (fuse & steer) | **Position *and* Mission** |

    The key difference from ACO: instead of feeding PX4 raw obstacle distances and
    letting *its* built-in logic brake, the board computes the **actual escape
    velocity** and PX4 just executes it. This works in **Mission mode too**.

---

## The idea in one picture

```
 Ascend-8tof (STM32H5)                                   PX4 (Ascend fork)
 ─────────────────────                                   ──────────────────
 8× VL53L8CX  ─► point cloud (body frame)
                72-sector polar histogram (VFH)
                pick the best open gap
                     │                                    ┌──────────────────────┐
   path blocked? ────┤ yes ─► velocity setpoint ─MAVLink─►│ accept + FUSE the     │
                     │        SET_POSITION_TARGET  (UART)  │ setpoint in Position/ │─► drone
                     │        (#84, BODY_NED)              │ Mission mode          │   deviates
                     └ no ──► send nothing ───────────────►│ setpoint goes stale → │─► resumes
                                                           │ mission/pilot resumes │   course
   ◄── ODOMETRY (velocity/attitude) ─────────────────────  └──────────────────────┘
```

The board only speaks up **while an obstacle is in the way**. When the path is
clear it goes silent, PX4's fusion times out, and the vehicle simply carries on
with whatever it was doing — a **temporary deviation**, not a takeover.

---

## Why a forked PX4?

Stock PX4 **only accepts external `SET_POSITION_TARGET` setpoints in Offboard
mode** — a full-authority mode with no mission or pilot in the loop. That's not
what we want: we want the mission (or the pilot) to stay in charge and only be
*nudged* around obstacles.

So Ascend maintains a small PX4 fork that adds one capability: **accept an
external avoidance setpoint and fuse it into Position and Mission mode.** It's a
narrow, surgical change:

- A new uORB topic (`external_avoidance_setpoint`) carries the incoming velocity.
- The MAVLink receiver mirrors an incoming `SET_POSITION_TARGET_LOCAL_NED` onto it.
- At the single point where **both** manual (Position) and auto (Mission) flight
  tasks produce their setpoint, the fork blends the external velocity in — and
  NaNs the matching position axis so the position controller doesn't fight the
  deviation.

The board owns *all* the intelligence (sensing + planning). PX4's only job is to
**accept and blend**. If the external stream stops, PX4 reverts instantly.

---

## What the board computes (VFH)

The avoidance planner is a **Vector Field Histogram** running on the STM32 — the
same algorithm whether it's flying the real vehicle or being tested in sim:

1. **Point cloud** — the 8× 8×8 ToF grids become 3-D points in the vehicle body
   frame (roll/pitch compensated from FC attitude; floor/ceiling returns rejected).
2. **Polar histogram** — points are binned into **72 sectors** (5° each) holding
   the nearest obstacle per direction.
3. **Gap selection** — if the direction of travel is blocked, it finds the
   nearest wide-enough open gap (with hysteresis so it doesn't dither).
4. **Setpoint** — it emits a **velocity toward that gap** (default: a lateral
   *strafe* that holds heading for the fastest clearance; an optional
   *steer-to-gap* variant turns the nose instead).

This is **reactive** (no global map) and **horizontal** — ideal for "don't hit
the thing in front of me," and light enough to run on the MCU.

---

## Flight behavior

=== "Position mode"
    The pilot flies normally. When they command motion toward an obstacle, the
    board's setpoint **deflects** that motion around it. Hands-off, the drone
    simply holds — there's no goal beyond the obstacle to continue toward, so
    avoidance is naturally coupled to the pilot commanding movement.

=== "Mission mode"
    The vehicle flies its waypoints. When an obstacle blocks a leg, the board
    steers around it; the moment the path clears, PX4 resumes flying **straight
    to the active waypoint** from wherever it ended up. The mission is never
    interrupted — Ascend's fork does the deviation, PX4's navigator keeps the goal.

!!! info "After it clears the obstacle"
    The vehicle **continues on a new straight line** — to the waypoint (Mission)
    or in the pilot's commanded direction (Position). It does **not** retrace the
    exact original track; there's no cross-track "return to line" step (that's an
    optional future addition).

---

## Interface & configuration

**On the wire (board → FC):** `SET_POSITION_TARGET_LOCAL_NED` (#84),
`MAV_FRAME_BODY_NED`, velocity (± yaw-rate) active, ~20 Hz, streamed **only while
avoiding**. Same UART link as the other MAVLink firmware.

**The FC also streams back** `ODOMETRY` (#331) so the board knows the vehicle's
velocity (its "direction of travel") and attitude.

**PX4 parameters** (on the Ascend fork):

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `EAV_EN` | `0` (off) | Enable fusion of the external avoidance setpoint |
| `EAV_TIMEOUT` | `0.5 s` | If no setpoint arrives within this, fusion stops and the mission/pilot setpoint resumes |

The MAVLink instance reading the board's UART must have **`forward_externalsp`
enabled** (PX4 only processes `SET_POSITION_TARGET` with it on).

---

## How it's validated — a "digital twin"

The exact firmware avoidance code is verified in **Gazebo** before it ever flies:

- A simulated drone carries **8 modelled ToF sensors** (8×8, 45° FoV, 4 m).
- A bridge process **runs the real firmware algorithm unchanged**, fed by the
  simulated sensors, and streams `SET_POSITION_TARGET` to a PX4 SITL running the
  fork — the same data path as the real vehicle. Only the I/O differs (sim topics
  instead of I²C, UDP instead of UART).

Because the thing under test is the *actual* on-board code, what passes in sim is
what runs on the vehicle. This is how the avoidance behavior is tuned and
regression-checked.

---

## Status

!!! warning "In active development"
    Setpoint-streaming avoidance and the PX4 fork are **in active development**.
    Reactive/horizontal only; validated in simulation and early flight. The
    default **sensor-stream firmware** remains the production path — talk to
    Ascend about enabling this mode.
