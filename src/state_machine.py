from machine import Timer

from leds import LEDs
from now import Now


class StateMachine:
    def __init__(
            self,
            leds: LEDs,
            cfg: dict,
            error_state_leds: str | None = None,
            blink_period: int = 1000,  # ms
            verbose: bool = True):
        self.leds = leds
        self.blink_period = blink_period
        self.verbose = verbose

        self.error_state = {
            'name': 'RULE_ERROR',
            'leds': 'all',
            'blink': True,
        }
        if error_state_leds is not None:
            self.error_state['leds'] = error_state_leds

        self._state = None
        self._last_date = None
        self._timer = None

        self.update_cfg(cfg)

    def update_cfg(self, cfg: dict, verbose: bool | None = None):
        self._cfg = cfg
        self._cfg_updated = True

    def _get_transitions_today(self, now):
        # get transitions (time, new state) for the current day

        rule = None

        for rule in self._cfg['rules']:
            if f'{now.year}-{now.month:02d}-{now.day:02d}' in rule.get('cond_date', []):
                break

            if now.weekday in rule.get('cond_weekday', []):
                break

        assert rule is not None

        if self.verbose:
            print(f'[StateMachine] using rule: {rule["name"]}')

        transitions = [((0, 0), self._cfg['states'][0])]

        for i, t in enumerate(rule['transitions']):
            if t is not None:
                t_unpacked = tuple(map(int, t.split(':')))
                transitions += [(t_unpacked, self._cfg['states'][i + 1])]

        return transitions

    def __call__(self, now: Now):
        if self._state == self.error_state and not self._cfg_updated:
            return

        if self._cfg_updated or now.date != self._last_date:
            try:
                self._transitions_today = self._get_transitions_today(now)

                if self.verbose:
                    print('[StateMachine] cfg updated')

            except Exception as ex:
                print(f'[StateMachine] ERROR parsing cfg: {ex}')
                self._transitions_today = None

            self._cfg_updated = False

        try:
            new_state = None

            while (len(self._transitions_today) > 0):
                next_time, next_state = self._transitions_today[0]

                if now.has_passed(*next_time):
                    new_state = next_state
                    self._transitions_today.pop(0)
                    continue

                break

            if new_state is not None:
                self._activate_state(new_state)

        except Exception as ex:
            print(f'[StateMachine] ERROR applying rules: {ex}')
            self._activate_state(self.error_state)

        self._last_date = now.date

    def _activate_state(self, state: dict):
        if self._state != state:
            if self.verbose:
                print(f'[StateMachine] activating state {state["name"]}')

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

