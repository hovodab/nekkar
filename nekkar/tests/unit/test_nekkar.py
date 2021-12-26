import timeit
from unittest import TestCase
from unittest.mock import Mock

from nekkar.core.limiter import ExecutionClient


class ExecutionClientTestCase(TestCase):

    @property
    def record_repository(self):
        repo = Mock(data={})
        repo.get = lambda key: repo.data.get(key)
        repo.update = lambda record: repo.data.update({record.id: record})
        repo.create = lambda record: repo.data.update({record.id: record})

        return repo

    @property
    def crt_lock(self):
        lock = Mock(data={})

        def acquire(record_id):
            if record_id in lock.data:
                return False
            else:
                lock.data[record_id] = True
                return True
        lock.acquire = acquire
        lock.release = lambda record_id: lock.data.pop(record_id)

        return lock

    def setUp(self) -> None:
        self.function = Mock()

    def test_interval(self):
        interval = 10
        self.client = ExecutionClient("exec1", 100, interval, self.function, self.crt_lock, self.record_repository)
        result = timeit.timeit(self.client, number=1)
        self.assertLess(result, interval / 1000)
        for i in range(99):
            result = timeit.timeit(self.client, number=1)
            self.assertAlmostEqual(result, interval / 1000, delta=0.001)

    def test_rate_limit(self):
        self.client = ExecutionClient("exec1", 100, 0, self.function, self.crt_lock, self.record_repository)
        self.client.RATE_LIMIT_TIME_UNIT = 1000
        for i in range(100):
            self.client()

        result = timeit.timeit(self.client, number=1)
        self.assertAlmostEqual(result, 1, delta=0.01)
