# Ascend Engineering Documentation

Technical documentation for Ascend Engineering hardware and software —
UAV companion computers, sensor systems, firmware, and integration guides.

<div class="grid cards" markdown>

-   :material-radar: **Ascend 8tof**

    ---

    360° time-of-flight obstacle-sensing system — an STM32H563 carrier board
    reading up to 8× VL53L8CX sensors and emitting a simple ASCII distance
    stream over UART that **any flight controller or onboard computer** can
    consume. Also runs an optional **on-board ACO collision-avoidance firmware**
    (MAVLink, beta). Hardware, power, comms, firmware, and integration (with a
    VOXL2 worked example).

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
