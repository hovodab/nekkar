import time
import random

from django.core.cache import cache


class DistributedLock(object):

    def __init__(self, key, limit):
        self._key = "{key}_LOCK".format(key=key)
        self._timestamp_key = "{key}_TIMESTAMP".format(key=key)
        self._locked = True
        self._delta = 60 / limit

    def __enter__(self):
        t = time.time()
        while not cache.add(self._key, True):
            time.sleep(random.uniform(0, 1))
        # print("#################################################### SLEEP TIME: {}".format(time.time() - t))
        self._locked = False
        print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._locked:
            cache.delete(self._key)
            print("RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR")

    def notify_start(self):
        current_time = time.time()
        last_value = float(cache.get(self._timestamp_key, current_time))
        print(f"------------last value: {last_value} --- current_time: {current_time}")
        if last_value < current_time:
            last_value = current_time
        next_run_time = last_value + self._delta
        cache.set(self._timestamp_key, next_run_time)
        return next_run_time - current_time
