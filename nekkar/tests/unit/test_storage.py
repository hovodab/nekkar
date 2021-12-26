import time
from unittest import TestCase
from unittest.mock import Mock

from nekkar.core.storage import CallableRecord
from nekkar.core.storage import CallableRecordRepository
from nekkar.core.storage import CRTLock


class CallableRecordRepositoryTestCase(TestCase):

    def setUp(self) -> None:
        self.cache = self.cache_mock
        self.repo = CallableRecordRepository(self.cache)

    @property
    def cache_mock(self):
        cache = Mock(data={})
        cache.get = lambda key: cache.data[key]
        cache.set = lambda key, value: cache.data.update({key: value})
        return cache

    def test_create(self):
        record = CallableRecord("method_name", [])
        self.repo.create(record)
        result = self.repo.get("method_name")

        self.assertEqual(record.name, result.name)
        self.assertEqual(record.hits_list, result.hits_list)
        self.assertIsInstance(result, CallableRecord)

    def test_update(self):
        record = CallableRecord("method_name", [])
        self.repo.create(record)
        record.hits_list.extend([111, 222])
        self.repo.update(record)
        result = self.repo.get("method_name")

        self.assertEqual(record.name, result.name)
        self.assertEqual(record.hits_list, result.hits_list)


class CRTLockTestCase(TestCase):

    def setUp(self) -> None:
        self.cache = self.cache_mock
        self.lifetime = 100
        self.lock = CRTLock(self.cache, self.lifetime)

    @property
    def cache_mock(self):
        cache = Mock(data={})
        cache.get = lambda key: cache.data[key]
        cache.delete = lambda key: cache.data.pop(key)
        cache.set = lambda key, value: cache.data.update({key: value})

        def add(key, value):
            if key in cache.data:
                return False
            cache.data[key] = value
            return True

        cache.add = add
        return cache

    def test_acquire_empty(self):
        first = self.lock.acquire("record_1")
        self.assertTrue(first)

    def test_acquire_occupied(self):
        self.lock.acquire("record_1")

        second = self.lock.acquire("record_1")
        self.assertFalse(second)

        another_first = self.lock.acquire("record_2")
        self.assertTrue(another_first)

    def test_acquire_zombie(self):
        self.lock.acquire("record_1")
        time.sleep((self.lifetime + 1) / 1000)

        second = self.lock.acquire("record_1")
        self.assertFalse(second)
        third = self.lock.acquire("record_1")
        self.assertTrue(third)

    def test_release(self):
        self.lock.acquire("record_1")

        second = self.lock.acquire("record_1")
        self.assertFalse(second)

        self.lock.release("record_1")

        third = self.lock.acquire("record_1")
        self.assertTrue(third)
