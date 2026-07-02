# Communications — UART Output

The board's interface to your system is a single **UART** on the host connector
(`J7`). With the **default firmware** it emits a plain **ASCII distance stream**
that any flight controller or onboard computer can read — this page is the
complete spec for that stream.

!!! note "Alternate firmware changes this link's protocol"
    The [**ACO firmware** variant (beta)](04-firmware.md#aco-firmware-onboard-collision-avoidance-beta)
    makes this same UART speak **MAVLink v2 at 115 200 baud** (running collision
    avoidance on-board and sending `OBSTACLE_DISTANCE` to a flight controller)
    instead of the ASCII stream below.

## Physical

- **Connector:** `J7` (see [Hardware → Host UART](01-hardware.md#host-uart-connector-j7-4-pin)).
  Board TX (pin 3) → host RX, GND (pin 4) → host GND.
- **Format:** 8 data bits, no parity, 1 stop bit (**8N1**), no flow control.
- **Direction:** one-way (board → host).

## Baud rate — important

Configure your host for **≈921 600 baud**.

- 921 600 is chosen because it's the fastest rate typical flight-controller UARTs
  and USB-UART adapters receive reliably.
- ⚠️ Some older material / a boot banner may mention **115 200** — that's stale.
  Use **921 600**.

## Wire format (ASCII)

For every sensor with new data, the board prints a header line then eight rows of
eight integers. Distances are in **millimetres**; **`0` means invalid / no
return** (see [Measurement validity](#measurement-validity)).

```
--- CH<n> ---
 1234  1230  1228 ...   (row 0: 8 space-padded integers, mm)
 ...                    (rows 1..7)
```

- Header: literal `--- CH` followed by the channel digit `0`–`7` and ` ---`.
- Each of the 8 rows: 8 integers → an **8×8 = 64-zone grid** for that channel,
  row-major, in the sensor's own frame.
- Frames stream at the ranging rate (**15 Hz** per sensor); channels are printed
  round-robin as each sensor reports new data.

So the full stream is, per channel, an **8×8 matrix of millimetre distances** —
one matrix per sensor, updating at 15 Hz.

### Reading it directly

Any serial terminal or a few lines of code will do — no special tooling:

```bash
# any serial terminal, 921600-8N1, e.g.
screen /dev/tty.usbserial-XXXX 921600
#   or:  minicom -D /dev/ttyUSB0 -b 921600
```

To turn the grids into 3-D points or obstacle data, see
[Integration](05-integration.md).

## Measurement validity

The board emits **`0` for any zone that is not a real measurement** (no/low
signal, out of range, etc.). Treat `0` as **"no return"**, never as "obstacle at
0 mm". All non-zero values are valid distances in millimetres.
