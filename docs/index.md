# Ascend Engineering documentation

Technical documentation for Ascend Engineering hardware and software. This includes UAV companion computers, sensor systems, firmware, and integration guides.

<div class="grid cards" markdown>

-   :material-radar: **Ascend 8tof**

    ---

    360° time-of-flight obstacle-sensing system. An STM32H563 carrier board that reads up to 8× VL53L8CX sensors and emits a simple ASCII distance stream over UART that **any flight controller or onboard computer** can consume. Also runs an optional **on-board ACO collision-avoidance firmware** (MAVLink, beta). Includes hardware, power, comms, firmware, and integration, with a VOXL2 worked example.

    [:octicons-arrow-right-24: Open the Ascend 8tof docs](ascend-8tof/index.md)

-   :material-cube-outline: **More coming**

    ---

    Additional hardware and software documentation will live here as it is written. Each product gets its own section in the left-hand navigation.

</div>

## About this site

- Every product has its own section in the sidebar and top tabs. Pick a product above or from the navigation to dive in.
- Documentation is maintained in the
  [`ascend-documentation`](https://github.com/AscendEngineering/ascend-documentation)
  repository. Pushes to `main` auto-deploy to this site.
- Questions or integration help? [:material-email: Contact Ascend Engineering](mailto:eng@ascendengineer.com){ .pill }
