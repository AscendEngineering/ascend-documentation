# Communications: UART output

The board exposes a single **UART** on the host connector (`J7`). With the **default firmware** it emits a plain **ASCII distance stream** that a flight controller or onboard computer can read. This page defines that stream.

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

## Baud rate: important

Configure your host for **≈921 600 baud**.

- 921 600 is the highest rate typical flight-controller UARTs and USB-UART adapters receive reliably.
- ⚠️ Some older material or a boot banner may mention **115 200**. That value is stale. Use **921 600**.

## Wire format (ASCII)

For every sensor with new data, the board prints a header line followed by eight rows of eight integers. Distances are in **millimetres**. **`0` means invalid or no return** (see [Measurement validity](#measurement-validity)).

```
--- CH<n> ---
 1234  1230  1228 ...   (row 0: 8 space-padded integers, mm)
 ...                    (rows 1..7)
```

- Header: literal `--- CH` followed by the channel digit `0` to `7` and ` ---`.
- Each of the 8 rows: 8 integers → an **8×8 = 64-zone grid** for that channel, row-major, in the sensor's own frame.
- Frames stream at the ranging rate (**15 Hz** per sensor). Channels are printed round-robin as each sensor reports new data.

The stream is, per channel, an **8×8 matrix of millimetre distances**. One matrix per sensor, updating at 15 Hz.

### Example output

A live capture looks like this. Each channel's 8×8 grid arrives in turn and the sequence repeats at 15 Hz. Here CH3 sees an object ~0.4 m dead center against a wall ~2 m out. CH5 sees mostly open space (`0` = no return):

```text
--- CH3 ---
  2015  2011  1998  1205  1199  1990  2005  2018
  2012  2004  1210   812   809  1201  1995  2010
  2008  1998   815   498   495   810  1988  2003
  1995  1201   495   402   399   492  1199  1996
  1990  1198   493   401   398   490  1197  1991
  2006  2000   818   500   497   812  1990  2004
  2013  2007  1215   820   817  1208  1998  2011
  2019  2014  2003  1220  1214  1996  2009  2021
--- CH4 ---
  3050  3044  3061  3072  3038  3040  3055  3066
  3041  3033  3052  3060  3029  3035  3049  3058
   ...   (8 rows total)
--- CH5 ---
     0     0     0     0     0     0     0     0
     0     0  3810  3805     0     0     0     0
     0     0  3798  3792     0     0     0     0
     0     0     0     0     0     0     0     0
     0     0     0     0     0     0     0     0
     0     0     0     0     0     0     0     0
     0     0     0     0     0     0     0     0
     0     0     0     0     0     0     0     0
```

Each value is a right-aligned integer (millimetres) in a fixed-width column, so columns line up and are whitespace-separated. Only channels with a connected, ranging sensor appear.

### Reading it directly

Any serial terminal or a few lines of code will do. No special tooling:

```bash
# any serial terminal, 921600-8N1, e.g.
screen /dev/tty.usbserial-XXXX 921600
#   or:  minicom -D /dev/ttyUSB0 -b 921600
```

To turn the grids into 3-D points or obstacle data, see
[Integration](05-integration.md).

## Measurement validity

The board emits **`0` for any zone that is not a real measurement** (no or low
signal, out of range, etc.). Treat `0` as **"no return"**, never as "obstacle at
0 mm". All non-zero values are valid distances in millimetres.
