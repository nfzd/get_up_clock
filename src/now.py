import time


class Date:
    def __init__(self, year: int, month: int, day: int):
        assert isinstance(year, int) and year > 0
        assert isinstance(month, int) and 1 <= month <= 12
        assert isinstance(day, int) and 1 <= month <= 31

        self.year = year
        self.month = month
        self.day = day

    def __eq__(self, other):
        return (self.year == other.year and
                self.month == other.month and
                self.day == other.day)


# TODO: rename to datetime
class Now:
    def __init__(self, localtime=None):
        if localtime is None:
            localtime = time.localtime()

        self._t = localtime

    @property
    def year(self):
        return self._t[0]

    @property
    def month(self):
        return self._t[1]

    @property
    def day(self):
        return self._t[2]

    @property
    def hour(self):
        return self._t[3]

    @property
    def minute(self):
        return self._t[4]

    @property
    def second(self):
        return self._t[5]

    @property
    def weekday(self):
        return self._t[6]

    @property
    def yearday(self):
        return self._t[7]

    @property
    def dst(self):
        return self._t[8]

    @property
    def date(self):
        return Date(self.year, self.month, self.day)

    def has_passed(self,
                   hour: int,
                   minute: int,
                   second: int = 0):
        if self.hour > hour:
            return True

        if self.hour == hour and self.minute > minute:
            return True

        if self.hour == hour and self.minute == minute and self.second >= second:
            return True

        return False

    def __str__(self):
        return f'{self.year}-{self.month:02d}-{self.day:02d}_{self.hour:02d}:{self.minute:02d}:{self.second:02d}'

