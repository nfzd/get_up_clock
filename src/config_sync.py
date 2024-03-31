from datetime import date, datetime

from logging import log as print
from wifi_manager import WifiManager


class ConfigSync:
    '''
    Online config syncing manager. Syncs config of one or multiple apps at
    specified times.

    Example:
            # init
            cfg_sync = ConfigSync(wifi_man, ("04:00", "16:00"))

            # register app
            url = "https://..."
            callback = lambda cfg: app.update(cfg)
            cfg_sync.register(url, callback)

            # force sync
            cfg_sync.sync(force=True)

            # call e.g. once per minute and this will sync twice per day (as
            # specified in init), returns config if successful, False if sync
            # failed, or None if sync was skipped
            cfg_sync.sync()

            # get success of last sync
            print(cfg_sync.synced)
    '''
    def __init__(self,
                 wifi_man: WifiManager,
                 sync_times: list[str],
                 verbose: bool = True):
        self.wifi_man = wifi_man
        self.sync_times = sync_times
        self._sync_times_today = None
        self.verbose = verbose

        self._last_sync_date = None
        self.synced = False

        self._registered_apps = []

    def _get_sync_times_today(self):
        sync_times_today = []
        today = date.today()

        for t in self.sync_times:
            sync_times_today += [datetime(
                today.year,
                today.month,
                today.day,
                *map(int, t.split(':')))]

        return sorted(sync_times_today)

    def register_app(self, url: str, callback: Callable):
        self._registered_apps += [(url, callback)]

    def sync(self, force: bool = False):
        '''
        Sync if time matches the defined sync times or we haven't synced before.
        '''
        sync = False
        now = datetime.now()
        today = now.date()

        if self._last_sync_date is None:
            sync = True

        if (
            self._last_sync_date is None or
            self._last_sync_date.year != today.year or
            self._last_sync_date.month != today.month or
            self._last_sync_date.day != today.day
        ):
            self._sync_times_today = self._get_sync_times_today()

        while (len(self._sync_times_today) > 0):
            if now >= self._sync_times_today[0]:
                sync = True
                self._sync_times_today.pop(0)
                continue

            break

        if not sync:
            return None

        self._last_sync_date = today

        success = self._sync()

        if not success:
            # sync failed, try again next time sync is run
            self._sync_times_today = [datetime.now()] + self._sync_times_today

        return success

    def _sync(self):
        self.synced = False

        if self.verbose:
            print('[ConfigSync] syncing NTP')

        # activate wifi and sync ntp

        if not self.wifi_man.connect():
            if self.verbose:
                print('[ConfigSync] no wifi connetion, aborting')
            return False

        # download config

        error = False

        if not self._registered_apps:
            if self.verbose:
                print('[ConfigSync] no apps registered')

        for url, callback in self._registered_apps:
            data = self.wifi_man.get_json(url)
            if data:
                callback(data)
            else:
                error = True

        # wrap up

        self.wifi_man.down()

        self.synced = not error

        return self.synced

