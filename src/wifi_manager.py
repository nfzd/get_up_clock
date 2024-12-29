import machine
import network
import ntptime
import time
import requests

from datetime import datetime
from logging import log as print


class WifiManager:
    '''
    Wifi manager handling wifi state, network discovery, pinging, and
    downloads. Also provides NTP syncing.
    '''
    def __init__(
        self,
        secrets: dict | list,
        tz_offset: int,
        auto_ntp_sync: bool = True,
        connect_timeout: int = 20,
        verbose: bool = True,
    ):
        if isinstance(secrets, dict):
            secrets = [secrets]

        self.__secrets = secrets
        self.tz_offset = tz_offset
        self.auto_ntp_sync = auto_ntp_sync
        self.connect_timeout = connect_timeout
        self.verbose = verbose

        # init

        self._wlan = network.WLAN(network.STA_IF)
        self._is_up = False
        self.down(verbose=False)

    @property
    def is_up(self):
        #return self._wlan.active()  # buggy, always returns True
        return self._is_up

    @property
    def is_connected(self):
        #return self._wlan.isconnected()  # buggy, returns True if e.g. no AP found
        return self._wlan.status() == network.STAT_GOT_IP

    def up(self, verbose: bool = None):
        if verbose is None:
            verbose = self.verbose

        if verbose:
            print(f'[Wifi] up')

        self._wlan.active(True)
        self._is_up = True

    def down(self, verbose: bool = None):
        if verbose is None:
            verbose = self.verbose

        if self.is_connected:
            self.disconnect(verbose=verbose)

        if verbose:
            print(f'[Wifi] down')

        self._wlan.active(False)
        self._is_up = False

    def scan(
        self,
        up: bool = True,
        verbose: bool = None,
    ):
        if verbose is None:
            verbose = self.verbose

        if not self.is_up and up:
            self.up(verbose=verbose)

        if verbose:
            print('[Wifi] scanning for networks')

        networks = self._wlan.scan()
        networks = [Network(net) for net in networks]
        networks = sorted(networks, key=lambda network: network.rssi, reverse=True)

        if verbose:
            for i, network in enumerate(networks):
                print(f'[Wifi] #{i}: ssid={network.ssid} rssi={network.rssi} channel={network.channel}')

        return networks

    def connect(
        self,
        up: bool = True,
        ntp_sync: bool = None,
        verbose: bool = None,
    ):
        if verbose is None:
            verbose = self.verbose

        if ntp_sync is None:
            ntp_sync = self.auto_ntp_sync

        if self.is_connected:
            return True

        if not self.is_up and up:
            self.up(verbose=verbose)

        assert self.is_up

        # find network to connect to

        networks = self.scan(up=up, verbose=False)

        ssid, password = None, None

        for net in networks:
            for s in self.__secrets:
                if net.ssid == s['ssid']:
                    ssid = net.ssid
                    password = s['pw']

        if ssid is None:
            print(f'[Wifi] ERROR: no known network found, cannot connect')
            return

        # connect

        if verbose:
            print(f'[Wifi] connecting to {ssid}')

        self._wlan.connect(ssid, password)

        wait = 0

        while wait < self.connect_timeout:
            wait += 1
            time.sleep(1)

            stat = self._wlan.status()

            if stat == network.STAT_CONNECT_FAIL:
                print('[Wifi] connect failed')
                break

            elif stat == network.STAT_NO_AP_FOUND:
                print('[Wifi] no AP found')
                break

            elif stat == network.STAT_GOT_IP:
                self.connected = True

                if self.verbose:
                    status = self._wlan.ifconfig()
                    print('[Wifi] connected, ip=' + status[0])

                break

        # sync ntp

        try:
            ntptime.settime()
            if self.verbose:
                print('[Wifi] NTP synced')
        except (OSError, OverflowError) as ex:
            if self.verbose:
                print(f'[Wifi] NTP sync failed: {ex}')
            return False

        t = time.localtime()

        if self.verbose:
            dt = datetime(None, None, None, localtime=t)
            print(f'[Wifi] utc={dt}')

        # correct for timezone and dst

        try:
            t = self.correct_time(t)
            machine.RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))

            if self.verbose:
                dt = datetime(None, None, None, localtime=t)
                print(f'[Wifi] localtime={dt}')

        except Exception as ex:
            print(f'[Wifi] ERROR setting time: {ex}')
            return False

        if verbose:
            ip = self._wlan.ifconfig()[0]
            print(f'[Wifi] connected, ip address: {ip}')

        return True

    def disconnect(
        self,
        verbose: bool = None,
    ):
        if verbose is None:
            verbose = self.verbose

        self._wlan.disconnect()

        if verbose:
            print('[Wifi] disconnected')

    def get(
        self,
        url: str,
        json: bool = False,
        connect: bool = True,
        down: bool = False,
        verbose: bool = None,
    ):
        if verbose is None:
            verbose = self.verbose

        if not self.is_connected and connect:
            self.connect(verbose=verbose)

        if not self.is_connected:
            print(f'[Wifi] [get] ERROR: cannot download, wifi not up')
            return None

        print(f'[Wifi] [get] downloading data from {url}')

        content = None

        try:
            response = requests.get(url)

            error_code = response.status_code

            print(f'[Wifi] [get] http error code {error_code}')

            if error_code == 200:
                content = response.json() if json else response.text

        except OSError as ex:
            print(f'[Wifi] [get] error: {ex}')

        if down:
            self.down(verbose=verbose)

        return content

    def get_json(
        self, *args,
        **kwargs,
    ):
        return self.get(*args, **kwargs, json=True)

    def ping(
        self,
        ip: str,
        up: bool = True,
        down: bool = False,
        verbose: bool = None,
    ):
        raise NotImplementedError()

    def correct_time(self, t):
        year = t[0]
        dst_on = time.mktime((year, 3, 31 - (int(5 * year / 4 + 4) % 7), 1, 0, 0, 0, 0, 0))
        dst_off = time.mktime((year, 10, 31 - (int(5 * year / 4 + 1)) % 7, 1, 0, 0, 0, 0, 0))

        now = time.time()

        if now < dst_on:
            s = self.tz_offset
        elif now < dst_off:
            s = self.tz_offset + 1
        else:
            s = self.tz_offset

        t = time.localtime(now + s * 3600)

        return t


class Network:
    def __init__(self, scan_results):
        data = list(scan_results)
        data[0] = data[0].decode()
        #data[1] = data[1].decode()
        self._data = data

    @property
    def ssid(self):
        return self._data[0]

    @property
    def channel(self):
        return self._data[2]

    @property
    def rssi(self):
        return self._data[3]

