import random
import time
from threading import RLock
from typing import Any

from nekkar.core.cache import BaseCache
from nekkar.core.exceptions import RetryMaxCountReached
from nekkar.core.storage import CallableRecord
from nekkar.core.storage import CallableRecordRepository
from nekkar.core.storage import CRTLock


class CacheRaceConditionResistantProxy(BaseCache):
    """
    Creates lock to avoid race conditions when using cache.
    """

    def __init__(self, cache: BaseCache):
        self._cache = cache
        self.lock = RLock()

    def add(self, key: str, value: Any) -> bool:
        with self.lock:
            return self._cache.add(key, value)

    def get(self, key: str) -> Any:
        with self.lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any):
        with self.lock:
            return self._cache.set(key, value)

    def delete(self, key: str):
        with self.lock:
            return self._cache.delete(key)


class Nekkar:

    def __init__(self, cache: BaseCache, auto_race_condition_resistance: bool = True):
        # Cache is shared between client calls.
        # So cache instance should work properly within multiple threads or the execution will fail.
        # auto_race_condition_resistance - will automatically lock the requests to the cache system to eliminate
        # this problem. Makes sense in case of multiple threads.
        if auto_race_condition_resistance:
            cache = CacheRaceConditionResistantProxy(cache)

        self._cache = cache

    def __call__(self, name: str, rate_limit: int, interval: int = None):
        """
        :name
        Every limited resource should has its own name.
        If the rate-limit for a service is general for all the methods/functions then use the same name for all methods.
        If the rate-limit for a service is method specific, then use different name for each method/function.

        :rate_limit
        Number that specifies how many calls to a method/function is allowed to make within 60 seconds.

        :interval
        Interval that should be considered when making requests. interval=None will automatically balance the requests.
        Despite what interval is provided the rate_limit will not be violated.

        E.g. rate_limit=10. "r(n)" means methods n-th execution. "--" means 6 seconds interval.
            interval=None
                |r1--r2--r3--r4--r5--r6--r7--r8--r9--r10--r11--r12...|
            interval=0
                |r1r2r3r4r5r6r7r8r9r10--------------------r11r12r13...|
            interval=12000
                |r1----r2----r3----r4----r5----r6----r7----r8----r9----r10----r11----r12...|
        """
        def decorator(function):
            def wrapper(*args, **kwargs):
                handler = ExecutionClient(
                    name=name,
                    rate_limit=rate_limit,
                    interval=interval,
                    function=function,
                    crt_lock=CRTLock(self._cache, 3000),
                    record_repository=CallableRecordRepository(self._cache)
                )
                return handler(*args, **kwargs)

            return wrapper
        return decorator


class ExecutionClient:
    # This implementation is NOT stateless.
    # Thus each call should has its own ExecutionClient instance.
    # Otherwise if single ExecutionClient instance work for multiple simultaneous function calls
    # there one client could interfere with another clients data.
    DEFAULT_TIMEOUT_MILLISECONDS = 50
    RATE_LIMIT_TIME_UNIT = 60000
    RETRY_MAX_COUNT = 1200

    def __init__(
        self,
        name: str,
        rate_limit: int,
        interval: int,
        function: callable,
        crt_lock: CRTLock,
        record_repository: CallableRecordRepository
    ):
        self._name = name
        self._rate_limit = rate_limit
        self._interval = int(self.RATE_LIMIT_TIME_UNIT / rate_limit) if interval is None else interval
        self._function = function
        self._record_repository = record_repository
        self._crt_lock = crt_lock
        self._retry_count = 0

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def execute(self, *args, **kwargs):
        while True:
            if not self._acquire_lock():
                self._sleep()
                self._retry_count += 1
                # TODO V2: Retry count, interval and sleep time are interconnected. So it makes sense to dynamically
                #  calculate the sleep time.
                if self._retry_count > self.RETRY_MAX_COUNT:
                    raise RetryMaxCountReached(
                        f"Can't acquire lock within {self.RETRY_MAX_COUNT} retries. Please check your configuration."
                    )
                continue

            try:
                record = self._record_repository.get(self._name)

                if record is None:
                    self._create_new_record()
                elif self._resource_available(record):
                    self._update_record(record)
                else:
                    continue
            finally:
                self._release_lock()

            result = self._execute(*args, **kwargs)
            return result

    def _execute(self, *args, **kwargs):
        return self._function(*args, **kwargs)

    def _sleep(self):
        start = self.DEFAULT_TIMEOUT_MILLISECONDS - 40
        end = self.DEFAULT_TIMEOUT_MILLISECONDS + 40
        delta = random.randrange(start, end) / 1000
        time.sleep(delta)

    def _timestamp(self):
        timestamp = time.time() * 1000
        return timestamp

    def _create_new_record(self):
        record = CallableRecord(
            name=self._name,
            hits_list=[self._timestamp()]
        )
        self._record_repository.create(record)
        return record

    def _update_record(self, record: CallableRecord):
        now = self._timestamp()
        index = 0
        for timestamp in record.hits_list:
            if now - timestamp < self.RATE_LIMIT_TIME_UNIT * 2:
                break
            index += 1

        record.hits_list = record.hits_list[index:]
        record.hits_list.append(now)
        self._record_repository.update(record)

    def _acquire_lock(self):
        return self._crt_lock.acquire(self._name)

    def _release_lock(self):
        self._crt_lock.release(self._name)

    def _resource_available(self, record: CallableRecord) -> bool:
        if not record.hits_list:
            ifh_ok = True
            thpm_ok = True
            secl_ok = True
        else:
            now = self._timestamp()
            last = record.hits_list[-1]
            ifh_ok = now - last > self._interval

            in_last_60 = [timestamp for timestamp in record.hits_list if now - timestamp < self.RATE_LIMIT_TIME_UNIT]
            thpm_ok = len(in_last_60) < self._rate_limit
            secl_ok = True  # TODO V2: Not implemented yet.

        result = thpm_ok and ifh_ok and secl_ok
        return result
