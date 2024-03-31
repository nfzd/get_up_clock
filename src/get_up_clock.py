import json
from machine import Timer

from leds import LEDs
from logging import log as print
from datetime import date, datetime


class GetUpClock:
    def __init__(
        self,
        leds: LEDs,
        error_state_leds: str = None,
        blink_period: int = 1000,  # ms
        cache_file: str = 'cache_clock.json',
        verbose: bool = True,
    ):
        self.leds = leds
        self.blink_period = blink_period
        self.cache_file = cache_file
        self.verbose = verbose

        self.error_state = {
            'name': 'RULE_ERROR',
            'leds': error_state_leds,
            'blink': True,
        }
        if error_state_leds is not None:
            self.error_state['leds'] = error_state_leds

        self._state = None
        self._last_date = None
        self._timer = None

        self.load_cache()

    def load_cache(self):
        if self.verbose:
            print(f'[GetUpClock] loading data from cache')

        try:
            with open(self.cache_file, 'r') as f:
                last_updated, data = json.load(f)

            self.last_updated = date(*map(int, last_updated.split('-')))
            self.data = data

        except (ValueError, OSError) as ex:
            print(f'[GetUpClock] ERROR: cannot load data from cache: {ex}')

            self.last_updated = None
            self.data = {}

    def write_cache(self, data, today):
        if self.verbose:
            print(f'[GetUpClock] writing data to cache')

        last_updated = f'{today.year}-{today.month:02d}-{today.day:02d}'

        try:
            with open(self.cache_file, 'w') as f:
                json.dump([last_updated, data], f)

        except OSError as ex:
            print(f'[GetUpClock] ERROR: cannot write data to cache: {ex}')

    def update_data(
        self,
        data,
    ):
        if self.verbose:
            print(f'[GetUpClock] updating data')

        if data:  # don't write to cache if download fails
            today = date.today()
            new_data = data != self.data

            self.last_updated = today

            if new_data:
                self.data = data
                self.write_cache(data, today)
                self.step(force_update=True)

    def _get_transitions_today(self, now: datetime):
        # get transitions (time, new state) for the current day

        rule = None

        for rule in self.data['rules']:
            if f'{now.year}-{now.month:02d}-{now.day:02d}' in rule.get('cond_date', []):
                break

            if now.weekday() in rule.get('cond_weekday', []):
                break

        assert rule is not None

        if self.verbose:
            print(f'[GetUpClock] using rule: {rule["name"]}')

        today = now.date()

        def get_datetime(h, m):
            return datetime(
                today.year,
                today.month,
                today.day,
                h,
                m)

        transitions = [(get_datetime(0, 0), self.data['states'][0])]

        for i, t in enumerate(rule['transitions']):
            if t is not None:
                t_unpacked = tuple(map(int, t.split(':')))
                transitions += [(get_datetime(*t_unpacked), self.data['states'][i + 1])]

        return transitions

    def step(
        self,
        now: datetime = None,
        *,
        force_update: bool = False,
    ):
        if now is None:
            now = datetime.now()

        if self._state == self.error_state and not force_update:
            return

        if force_update or self._last_date is None or now.date() != self._last_date:
            try:
                self._transitions_today = self._get_transitions_today(now)

                if self.verbose:
                    print('[GetUpClock] transitions loaded')

            except Exception as ex:
                print(f'[GetUpClock] ERROR parsing cfg: {ex}')
                self._transitions_today = None

        try:
            new_state = None

            while (len(self._transitions_today) > 0):
                next_time, next_state = self._transitions_today[0]

                if now >= next_time:
                    new_state = next_state
                    self._transitions_today.pop(0)
                    continue

                break

            if new_state is not None:
                self._activate_state(new_state)

        except Exception as ex:
            print(f'[GetUpClock] ERROR applying rules: {ex}')
            self._activate_state(self.error_state)

        self._last_date = now.date()

    def _activate_state(self, state: dict):
        if self._state != state:
            if self.verbose:
                print(f'[GetUpClock] activating state {state["name"]}')

            if self._timer is not None:
                self._timer.deinit()
                self._timer_toggle_leds = None

            self.leds.all.off()

            if state['leds']:
                if state['blink']:
                    self._timer_toggle_leds = state['leds']
                    self._timer = Timer(
                        mode=Timer.PERIODIC,
                        period=self.blink_period,
                        callback=self._timer_callback)
                else:
                    for group in state['leds'].split(','):
                        getattr(self.leds, group).on()

            self._state = state

    def _timer_callback(self, t):
        for group in self._timer_toggle_leds.split(','):
            getattr(self.leds, group).toggle()

