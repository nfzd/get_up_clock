import time


class date:  # lower case to match python lib
    def __init__(self, year: int, month: int, day: int):
        assert isinstance(year, int) and year > 0
        assert isinstance(month, int) and 1 <= month <= 12
        assert isinstance(day, int) and 1 <= month <= 31

        self.year = year
        self.month = month
        self.day = day

    @classmethod
    def today(cls):
        lt = time.localtime()
        return cls(lt[0], lt[1], lt[2])

    def __eq__(self, other):
        return (
            self.year == other.year and
            self.month == other.month and
            self.day == other.day)

    def __lt__(self, other):
        return (
            self.year < other.year or
            (self.year == other.year and self.month < other.month) or
            (self.year == other.year and self.month == other.month and self.day < other.day)
        )

    def __gt__(self, other):
        return not (self < other or self == other)

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return not self < other


class datetime:  # lower case to match python lib
    def __init__(
            self,
            year: int,
            month: int,
            day: int,
            hour: int = 0,
            minute: int = 0,
            second: int = 0,
            *,
            localtime: tuple = None,
    ):
        if localtime is None:
            assert year >= 2000

            # get weekday
            wd = 5  # reference: weekday of 2000-01-01

            def is_leap_year(y):
                return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

            for y in range(2000, year):
                if not is_leap_year(y):
                    wd += 1

            for m in range(1, month):
                if m in (1, 3, 5, 7, 8, 10, 12):
                    wd += 3
                elif m in (4, 6, 9, 11):
                    wd += 2
                elif is_leap_year(year):
                    wd += 1

            wd = (wd + day - 1) % 7

            localtime = (year, month, day, hour, minute, second, wd, None, None)

        self._t = localtime

    @classmethod
    def now(cls):
        lt = time.localtime()
        return cls(None, None, None, localtime=lt)

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

    def weekday(self):  # method to match python lib
        return self._t[6]

    def timetuple(self):  # method to match python lib
        return self._t

    def date(self):  # method to match python lib
        return date(self.year, self.month, self.day)

    def __eq__(self, other):
        return self._t[:6] == other._t[:6]

    def __lt__(self, other):
        return (
            (self._t[0] < other._t[0]) or
            (self._t[:1] == other._t[:1] and self._t[1] < other._t[1]) or
            (self._t[:2] == other._t[:2] and self._t[2] < other._t[2]) or
            (self._t[:3] == other._t[:3] and self._t[3] < other._t[3]) or
            (self._t[:4] == other._t[:4] and self._t[4] < other._t[4]) or
            (self._t[:5] == other._t[:5] and self._t[5] < other._t[5])
        )

    def __gt__(self, other):
        return not (self < other or self == other)

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return not self < other

    def __str__(self):
        return f'{self.year}-{self.month:02d}-{self.day:02d}_{self.hour:02d}:{self.minute:02d}:{self.second:02d}'

    def compact_fmt(self):
        return f'{self.year}{self.month:02d}{self.day:02d}_{self.hour:02d}{self.minute:02d}{self.second:02d}'

