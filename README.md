# Raspberry Pi Pico W *Get Up Ok* clock with web-based configuration

A simple [Pico W](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)-based clock indicating with colored LEDs whether or not getting up is a good idea. Wifi is used for time sync (NTP) and configuration specification.

Uses a state machine with can be configured via a config file on the web. Supports weekday and date-specific rules. See `config/cfg.json` and below for details.

## Setup

* Connect some LEDs to the GPIO pins (with, e.g., a 470R in series).
* Change `src/main.py`: define the pin groups (one or multiple LEDs for every state).
* Create a config defining the desired states (with led groups on or blinking and state transition times), upload it wherever it makes sense.
* Add wifi credentials, config URL, sync times, and time zone offset to `src/secrets.py`.
* Copy all `.py` files in `src` to the board and run.

Note: with a fresh Pico, you need to install MicroPython first. See the [docs](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html).

## Configuration

See `config/cfg-leds.json` and `config/cfg-neopixel.json` for examples.

### Simple LEDS

Here, we use the following LED specification in `src/main.py`:

```python
leds = LEDs(status='LED', red=(14, 15), green=(16, 17), test_all=True)
```

Here we have two groups of two LEDs each, simply named for their colors. These group names are used in the configuration to specify what should happen at which time.

The configuration is a JSON dict with two keys: `states` and `rules`. The former defines which states exist, e.g.:

```json

    "states": [
        {
           "name": "NIGHT2",
           "leds": "red"
        },
        {
           "name": "CAN_GET_UP",
           "leds": "green"
        },
        {
           "name": "MUST_GET_UP",
           "leds": "green",
           "blink": true
        },
        {
           "name": "DAY"
        },
        {
           "name": "NIGHT1",
           "leds": "red"
        }
    ],
```

Here, there are 5 states: NIGHT2, CAN_GET_UP, MUST_GET_UP, DAY, and NIGHT1. The states must be defined in the correct (static) order. The first and last states define the state during the night (here: red LEDS, not blinking). Two states are needed for the night as the first state always starts at 00:00 and the last state always ends at 23:59. Then, there is a state with green LEDs on (CAN_GET_UP), one with green LEDs blinking (MUST_GET_UP), and the DAY state during which all LEDs are off.

Note that states can be skipped, see below.

The example config includes three rules:

```json
    "rules": [
        {
            "name": "holidays_2024",
            "cond_date": [
                "2024-12-24",
                "2024-12-25",
                "2024-12-26",
                "2024-12-27",
                "2024-12-28",
                "2024-12-29",
                "2024-12-30",
                "2024-12-31"
            ],
            "transitions": [
                "07:00",
                null,
                "09:00",
                "19:00"
            ]
        },
        {
            "name": "default_weekend",
            "cond_weekday": [5, 6],
            "transitions": [
                "07:00",
                null,
                "08:00",
                "19:00"
            ]
        },
        {
            "name": "default_weekday",
            "transitions": [
                "06:30",
                "07:00",
                "08:00",
                "19:00"
            ]
        }
    ]
```

Every day, the rules are checked in order, and the first rule whose conditions are met is applied. Two condition types are supported: `cond_date` (with a list of exact dates in YYYY-MM-DD format) and `cond_weekday` (with a list of 0-based weekday indices).

For each rule, the transitions times can be specified. The first state always begins at 00:00. The first time specified in the transition list defines the time of switching from the first to the second state (and so on). A transition time can be set to `null`, in which case the state will be skipped (here, the MUST_GET_UP state is skipped for rules `holidays_2024` and `default_weekend`).

Note: state and rule names are only used for logging / debugging.

### Neopixel

When using a NeoPixel, the following LED specification in `src/main.py` could be used:

```python
leds = NeoPixel(Pin(22), 1)
```

In this case, states can be defined as follows:

```json

    "states": [
        {
           "name": "NIGHT2",
           "color": "#ff0000",
           "luminosity": 0.4
        },
        {
           "name": "CAN_GET_UP",
           "color": "#00ff00",
           "luminosity": 0.4
        },
        {
           "name": "MUST_GET_UP",
           "color": "#00ffff",
           "blink": true
        },
        {
           "name": "DAY"
        },
        {
           "name": "NIGHT1",
           "color": "#ff0000",
           "luminosity": 0.4
        }
    ],
```

If no luminosity is specified, the maximum intensity is used.

See above for how to define rules.
