import json
import micropython
from machine import Timer

from datetime import datetime
from config_sync import ConfigSync
from leds import LEDs
from secrets import cfg_url, secrets, sync_times, tz_offset
from get_up_clock import GetUpClock
from wifi_manager import WifiManager


# ----------------------------------------------------------------------
# setup board

micropython.alloc_emergency_exception_buf(100)

# ----------------------------------------------------------------------
# configuration

#
# Define LED groups with a descriptive name (here: 'red' and 'green'), each
# controlled by one or multiple GPIO pins. The groups are used in the state
# config file.
#
leds = LEDs(status='LED', red=(14, 15), green=(16, 17), test_all=True)

#
# Define wifi SSID and password as well as time zone offset in secrets.py
# (note: can add multiple networks).
#
wifi_man = WifiManager(secrets, tz_offset)
wifi_man.connect()  # ntp sync

#
# Define the sync times in secrets.py.
#
cfg_sync = ConfigSync(wifi_man, sync_times)

#
# Use some of the LED group names defined above here, these groups will blink
# together if a config error (parsing or applying) occured.
#
app = GetUpClock(
    leds,
    error_state_leds='night,day')
cfg_sync.register_app(cfg_url, app.update_data)

#
# Run initial sync.
#
cfg_sync.sync(force=True)

#
# Setup timer for blinking status LED in case of sync error.
#
sync_error_cycle_count = 0

def sync_error_callback(t):
    global sync_error_cycle_count

    if cfg_sync.synced:
        sync_error_cycle_count = 0
    else:
        sync_error_cycle_count += 1
        if sync_error_cycle_count > 23:
            leds.status.on()
        if sync_error_cycle_count > 24:
            leds.status.off()
            sync_error_cycle_count = 0

sync_error_timer = Timer(
    mode=Timer.PERIODIC,
    period=200,
    callback=sync_error_callback)

# ----------------------------------------------------------------------
# main loop

last_iter_sec = -1
last_iter_min = -1

while True:
    # run update functions max once per second
    now = datetime.now()

    if now.minute != last_iter_min:
        last_iter_min = now.minute

        cfg_sync.sync()  # if necessary

    if now.second != last_iter_sec:
        last_iter_sec = now.second

        app.step(now)

