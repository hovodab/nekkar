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
        print("#################################################### SLEEP TIME: {}".format(time.time() - t))
        self._locked = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._locked:
            cache.delete(self._key)

    def notify_start(self):
        current_time = time.time()
        last_value = float(cache.get(self._timestamp_key, current_time - self._delta))
        if last_value + self._delta < current_time:
            last_value = current_time - self._delta
        last_value += self._delta
        cache.set(self._timestamp_key, last_value)
        return last_value - current_time
