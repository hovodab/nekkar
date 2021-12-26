import json
from unittest import TestCase
from unittest.mock import patch

from nekkar.core.cache import MemcachedCache


class MemcachedCacheTestCase(TestCase):
    # This test case is almost useless.

    def setUp(self) -> None:
        self.host = "localhost"
        self.port = 11211

    @property
    def cache(self):
        return MemcachedCache(self.host, self.port)

    @patch("core.cache.base_cache.Client")
    def test_set_simple(self, client):
        self.cache.set("KEY1", "VALUE")
        client((self.host, self.port)).set.assert_called_with("KEY1", '"VALUE"')

    @patch("core.cache.base_cache.Client")
    def test_set_container(self, client):
        value = {"key": "value", "lst": [1, 2]}
        self.cache.set("KEY1", value)
        expected = json.dumps(value)
        client((self.host, self.port)).set.assert_called_with("KEY1", expected)

    @patch("core.cache.base_cache.Client")
    def test_delete(self, client):
        self.cache.delete("KEY1")
        client((self.host, self.port)).delete.assert_called_with("KEY1")

    @patch("core.cache.base_cache.Client")
    def test_get(self, client):
        client((self.host, self.port)).get.return_value = json.dumps({"key": "value"})
        result = self.cache.get("KEY1")
        self.assertEqual(result, {"key": "value"})

    @patch("core.cache.base_cache.Client")
    def test_add(self, client):
        value = {"key": "value", "lst": [1, 2]}
        self.cache.add("KEY1", value)
        expected = json.dumps(value)
        client((self.host, self.port)).add.assert_called_with("KEY1", expected, noreply=False)
