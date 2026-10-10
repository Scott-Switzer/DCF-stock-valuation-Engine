"""A manually advanced clock for deadline tests.

Tests replace the ``time`` module used by ``dcf_loader`` with ``clock.module()``.
Work that would take time calls ``clock.advance(seconds)`` instead of sleeping,
so deadline expiry happens at an exact step rather than by wall-clock race.
"""

from types import SimpleNamespace


class FakeClock:
    def __init__(self, start=1000.0):
        self.now = float(start)

    def monotonic(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds

    def module(self):
        # JsonHTTP reads time.monotonic(); nothing in these tests sleeps for real.
        return SimpleNamespace(monotonic=self.monotonic, sleep=self.advance)
