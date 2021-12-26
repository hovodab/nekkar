import time
from typing import List
from typing import Optional

from nekkar.core.cache import BaseCache


class CallableRecord:
    """
    A record in the storage which is shared between calling clients. Stores information about single limited resource.
    """

    def __init__(self, name: str, hits_list: List[float], count_in_progress: Optional[int] = 0):
        self._name = name
        self._hits_list = hits_list
        self._count_in_progress = count_in_progress

    @property
    def id(self):
        return self._name

    @property
    def name(self):
        return self._name

    @property
    def hits_list(self):
        return self._hits_list

    @hits_list.setter
    def hits_list(self, hits):
        self._hits_list = hits

    @property
    def count_in_progress(self):
        return self._count_in_progress


class CallableRecordRepository:
    """
    Provides CallableRecords persistence methods.
    """

    def __init__(self, cache: BaseCache):
        self._cache = cache

    def _dict_to_record(self, data: dict) -> CallableRecord:
        record = CallableRecord(
            name=data["name"],
            hits_list=data["hits_list"],
            count_in_progress=data["count_in_progress"],
        )
        return record

    def _record_to_dict(self, record: CallableRecord) -> dict:
        data = {
            "name": record.name,
            "hits_list": record.hits_list,
            "count_in_progress": record.count_in_progress
        }
        return data

    def get(self, record_id: str) -> Optional[CallableRecord]:
        data = self._cache.get(record_id)
        if data is None:
            return None

        record = self._dict_to_record(data)
        return record

    def create(self, record: CallableRecord):
        data = self._record_to_dict(record)
        self._cache.set(key=record.id, value=data)

    def update(self, record: CallableRecord):
        self.create(record)


class CRTLock:
    """
    Shared lock by specific ID.
    """

    def __init__(self, cache: BaseCache, lifetime: float):
        """
        lifetime: In milliseconds.
        """
        self._cache = cache
        self._lifetime = lifetime

    def _record_key(self, record_id: str) -> str:
        key = f"{record_id}-RECORD_LOCK_KEY"
        return key

    def _timestamp(self):
        timestamp = time.time() * 1000
        return timestamp

    def acquire(self, record_id: str) -> bool:
        key = self._record_key(record_id)
        acquired = self._cache.add(key, self._timestamp())
        if acquired:
            return True

        # Check if is ZOMBIE, if yes then release.
        timestamp = self._cache.get(key)
        # Could be released just now, if yes then there is nothing to do.
        if timestamp is None:
            return False

        if self._timestamp() - timestamp > self._lifetime:
            self.release(record_id)

        return False

    def release(self, record_id: str):
        key = self._record_key(record_id)
        self._cache.delete(key)
