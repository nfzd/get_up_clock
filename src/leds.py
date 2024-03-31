from machine import Pin
from time import sleep


class LEDs:
    '''
    Multi-LED wrapper class.

    Provide names and pin numbers (or "LED" for status LED) as kwargs during
    init. Can pass multiple pins which will be controlled together.


    Example:

            leds = LEDs(red=(14, 15), green=16, status="LED")
            leds.red.on()
            leds.status.toggle()
    '''
    def __init__(self,
                 *,
                 test_all: bool = False,
                 verbose: bool = True,
                 **kwargs):
        self.verbose = verbose

        all_pins = []

        for name, pins in kwargs.items():
            led = LEDGroup(pins)
            setattr(self, name, led)
            all_pins += led._leds

        self.all = LEDGroup(list(set(all_pins)))

        if test_all:
            self.test_all()
        else:
            self.all.off()

    def test_all(self):
        if self.verbose:
            print('[LEDs] testing all')

        self.all.off()
        sleep(1)

        for led in self.all._leds:
            led.on()
            sleep(1)
            led.off()

        if self.verbose:
            print('[LEDs] testing all done')


class LEDGroup:
    '''
    Wrapper class for multiple LEDs which should be controlled together.
    '''
    def __init__(self, pins):
        assert isinstance(pins, (int, str, tuple, list)), 'Need to pass one or more pins as int, str, tuple, or list'

        if isinstance(pins, (int, str)):
            pins = (pins,)

        self._leds = []

        for pin in pins:
            if isinstance(pin, Pin):
                led = pin
            else:
                led = Pin(pin, Pin.OUT)
            self._leds += [led]

    def on(self):
        for led in self._leds:
            led.on()

    def off(self):
        for led in self._leds:
            led.off()

    def toggle(self):
        for led in self._leds:
            led.toggle()

