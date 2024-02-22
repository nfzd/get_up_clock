import json
import machine
import ntptime
import time
import requests

from now import Now
from wifi import Wifi


class ConfigSync:
    '''
    Online config and NTP syncing manager. Requires a Wifi instance passed to
    __init__().

    Example:
            # init
            cfg_sync = ConfigSync(wifi, ("04:00", "16:00"))

            # force sync
            cfg_sync.sync()

            # call e.g. once per minute and this will sync twice per day (as
            # specified in init), returns config if successful, False if sync
            # failed, or None if sync was skipped
            cfg_sync.sync_maybe(now)

            # get success of last sync
            print(cfg_sync.synced)
    '''
    def __init__(self,
                 wifi: Wifi,
                 sync_times: list[str],
                 cfg_url: str,
                 verbose: bool = True):
        self._wifi = wifi
        self.sync_times = sync_times
        self._sync_times_today = self._parse_sync_times()
        self.cfg_url = cfg_url
        self.verbose = verbose

        self._last_sync_date = None
        self._cfg_file = 'cfg.json'
        self.synced = False

        # load old config

        try:
            with open(self._cfg_file) as f:
                self._cfg = json.load(f)

        except Exception as ex:
            print(f'[ConfigSync] ERROR loading old config: {ex}')
            self._cfg = None

    def _parse_sync_times(self):
        sync_times_today = []

        for t in self.sync_times:
            sync_times_today += [tuple(map(int, t.split(':')))]

        return sorted(sync_times_today, key=lambda x: 60 * x[0] + x[1])

    def sync_maybe(self, now: Now):
        '''
        Sync if time matches the defined sync times or we haven't synced before.
        '''
        sync = False
        now_date = now.date

        if self._last_sync_date is None:
            sync = True
        else:
            if self._last_sync_date != now_date:
                self._sync_times_today = self._parse_sync_times()

            while (len(self._sync_times_today) > 0):
                if now.has_passed(*self._sync_times_today[0]):
                    sync = True
                    self._sync_times_today.pop(0)
                    continue

                break

        if not sync:
            return None

        self._last_sync_date = now_date
        return self.sync()

    def sync(self):
        self.synced = False

        if self.verbose:
            print('[ConfigSync] syncing NTP')

        # activate wifi and sync

        if not self._wifi.connect():
            if self.verbose:
                print('[ConfigSync] no wifi connetion, aborting')
            return False

        try:
            ntptime.settime()
            if self.verbose:
                print('[ConfigSync] NTP synced')
        except OSError as ex:
            if self.verbose:
                print(f'[ConfigSync] NTP sync failed: {ex}')
            return False

        t = time.localtime()

        if self.verbose:
            print(f'[ConfigSync] utc={Now(t)}')

        # correct for timezone and dst

        try:
            t = self.correct_time(t)
            machine.RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))

            if self.verbose:
                print(f'[ConfigSync] localtime={Now()}')

        except Exception as ex:
            print(f'[ConfigSync] ERROR setting time: {ex}')
            return False

        # download config

        try:
            response = requests.get(url=self.cfg_url)
            cfg = response.json()

            if self.verbose:
                print(f'[ConfigSync] cfg downloaded')

            if cfg != self._cfg:
                with open(self._cfg_file, 'w') as f:
                    json.dump(cfg, f)

            self._cfg = cfg

        except Exception as ex:
            print(f'[ConfigSync] ERROR getting config: {ex}')
            return False

        # wrap up

        self._wifi.disconnect()

        self.synced = True

        return cfg

    def correct_time(self, t):
        year = t[0]
        dst_on = time.mktime((year, 3, 31 - (int(5 * year / 4 + 4) % 7), 1, 0, 0, 0, 0, 0))
        dst_off = time.mktime((year, 10, 31 - (int(5 * year / 4 + 1)) % 7, 1, 0, 0, 0, 0, 0))

        now = time.time()

        if now < dst_on:
            t = time.localtime(now + 3600)  # UTC + 1
        elif now < dst_off:
            t = time.localtime(now + 2 * 3600)  # UTC + 2
        else:
            t = time.localtime(now + 3600)  # UTC + 1

        return t

    @property
    def cfg(self):
        return self._cfg

