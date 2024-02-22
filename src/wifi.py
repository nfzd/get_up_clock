from machine import Pin
import network
from time import sleep


class Wifi:
    '''
    Wifi managing class. Pass a dict containing keys 'ssid' and 'pw' to
    __init__() for network access.

    Example:
            secrets = {'ssid': 'Network', 'pw': 123}
            wifi = Wifi(secrets)
            wifi.connect()
            print(wifi.connected)  # True if connection was established
            wifi.disconnect()
    '''
    def __init__(self,
                 secrets: dict,
                 status_led: Pin | None = None,
                 connect_attempts: int = 5,
                 connect_timeout: int = 20,
                 verbose: bool = True):
        self.secrets = secrets
        self.status_led = status_led
        self.connect_attempts = connect_attempts
        self.connect_timeout = connect_timeout
        self.verbose = verbose

        self._wlan = network.WLAN(network.STA_IF)
        self.connected = False

    def connect(self):
        if not self.connected:
            self._connect()

        return self.connected

    def reconnect(self):
        if self.connected:
            self._disconnect()

        return self._connect()

    def disconnect(self):
        if self.connected:
            return self._disconnect()

    def _connect(self):
        self.connected = False
        if self.status_led is not None:
            self.status_led.off()

        if self.verbose:
            print('[Wifi] connecting')

        self._wlan.active(True)
        self._wlan.connect(self.secrets['ssid'], self.secrets['pw'])

        for attempt in range(self.connect_attempts):
            if self.verbose:
                print(f'[Wifi] attempt {attempt+1}/{self.connect_attempts}')

            wait = 0

            while wait < self.connect_timeout:
                wait += 1
                sleep(1)

                stat = self._wlan.status()

                if stat == network.STAT_CONNECT_FAIL:
                    print('[Wifi] connect failed')
                    break

                elif stat == network.STAT_NO_AP_FOUND:
                    print('[Wifi] no AP found')
                    break

                elif stat == network.STAT_GOT_IP:
                    self.connected = True
                    if self.status_led is not None:
                        self.status_led.on()

                    if self.verbose:
                        status = self._wlan.ifconfig()
                        print('[Wifi] connected, ip=' + status[0])

                    break

            if self.connected:
                break

        return self.connected

    def _disconnect(self):
        if self.verbose:
            print('[Wifi] disconnecting')

        self._wlan.active(False)
        self.connected = False
        if self.status_led is not None:
            self.status_led.off()

        return True

