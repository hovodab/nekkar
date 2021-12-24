import json
from abc import ABCMeta
from abc import abstractmethod
from typing import Any

from pymemcache.client import base as base_cache


class BaseCache(metaclass=ABCMeta):

    @abstractmethod
    def add(self, key: str, value: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any):
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str):
        raise NotImplementedError


class MemcachedCache(BaseCache):

    def __init__(self, host, port):
        self._client = base_cache.Client((host, port))

    def add(self, key: str, value: Any) -> bool:
        value = json.dumps(value)
        result = self._client.add(key, value, noreply=False)
        return result

    def get(self, key: str) -> Any:
        result = self._client.get(key)
        if result is None:
            return result
        result = json.loads(result)
        return result

    def set(self, key: str, value: Any):
        value = json.dumps(value)
        self._client.set(key, value)

    def delete(self, key: str):
        self._client.delete(key)
