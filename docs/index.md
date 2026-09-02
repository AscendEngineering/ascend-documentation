# Ascend Engineering Documentation

Technical documentation for Ascend Engineering hardware and software —
UAV companion computers, sensor systems, firmware, and integration guides.

<div class="grid cards" markdown>

-   :material-radar: **Ascend 8tof v2**

    ---

    360° time-of-flight obstacle-sensing system — a 30 × 30 mm STM32H563 carrier
    board reading 8× VL53L8CX sensors and emitting **MAVLink
    `OBSTACLE_DISTANCE`** straight into **stock PX4 collision prevention**, plus
    a binary 512-zone point cloud on request. Hardware, pinouts, power, comms,
    firmware, and integration (with a VOXL2 worked example).

    [:octicons-arrow-right-24: Open the Ascend 8tof docs](ascend-8tof/index.md)

-   :material-cube-outline: **More coming**

    ---

    Additional hardware and software documentation will live here as it's
    written — each product gets its own section in the left-hand navigation.

</div>

## About this site

- Every product has its own section in the sidebar (and top tabs); pick a
  product above or from the navigation to dive in.
- Documentation is maintained in the
  [`ascend-documentation`](https://github.com/AscendEngineering/ascend-documentation)
  repository; pushes to `main` auto-deploy to this site.
- Questions or integration help? [:material-email: Contact Ascend Engineering](mailto:eng@ascendengineer.com){ .pill }
