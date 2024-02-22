import json
import micropython
from machine import Timer

from config_sync import ConfigSync
from leds import LEDs
from now import Now
from secrets import cfg_url, secrets
from state_machine import StateMachine
from wifi import Wifi


# configuration

#
# Define LED groups with a descriptive name (here: 'red' and 'green'), each
# controlled by one or multiple GPIO pins. The groups are used in the state
# config file.
#
leds = LEDs(status='LED', red=(14, 15), green=(16, 17), test_all=True)

#
# Define wifi SSID and password in secrets.py.
#
wifi = Wifi(secrets)

#
# Define the times at which both board time and configuration will be synced
# every day.
#
cfgsync = ConfigSync(
    wifi,
    sync_times=('03:59', '11:59', '19:59'),
    cfg_url=cfg_url)

#
# Use some of the LED group names defined above here, these groups will blink
# together if a config error (parsing or applying) occured.
#
state_machine = StateMachine(
    leds,
    cfgsync.cfg,
    error_state_leds='red,green')

# ----------------------------------------------------------------------
# setup board

micropython.alloc_emergency_exception_buf(100)

# main loop

last_iter_sec = -1
last_iter_min = -1
sync_error_timer = None

while True:
    # run update functions max once per second
    now = Now()

    if now.second != last_iter_sec:
        last_iter_sec = now.second

        state_machine(now)

    if now.minute != last_iter_min:
        last_iter_min = now.minute

        cfg = cfgsync.sync_maybe(now)

        if cfg is None:
            pass  # sync skipped

        elif cfg is False:
            # sync error
            if sync_error_timer is None:
                sync_error_timer = Timer(
                    mode=Timer.PERIODIC,
                    period=500,
                    callback=lambda t: leds.status.toggle())

        else:
            # sync successful
            if sync_error_timer is not None:
                sync_error_timer.deinit()
                sync_error_timer = None

            state_machine.update_cfg(cfg)

