from unittest import TestCase

from nekkar.core.cache import MemcachedCache


class MemcachedCacheIntegrationTestCase(TestCase):

    def setUp(self) -> None:
        self.host = "localhost"
        self.port = 11211

    @property
    def cache(self):
        return MemcachedCache(self.host, self.port)

    def test_set_simple(self):
        self.cache.set("KEY1", "VALUE")

        result = self.cache.get("KEY1")
        self.assertEqual(result, "VALUE")

    def test_set_container(self):
        value = {"key": "value", "lst": [1, 2]}
        self.cache.set("KEY1", value)

        result = self.cache.get("KEY1")
        self.assertEqual(result, value)

    def test_delete(self):
        self.cache.delete("KEY1")

        result = self.cache.get("KEY1")
        self.assertIsNone(result)

    def test_get(self):
        self.cache.set("KEY1", "V1")
        result = self.cache.get("KEY1")
        self.assertEqual(result, "V1")

    def test_add_free(self):
        self.cache.delete("KEY1")
        value = {"key": "value", "lst": [1, 2]}
        result = self.cache.add("KEY1", value)

        self.assertEqual(self.cache.get("KEY1"), value)
        self.assertTrue(result)

    def test_add_(self):
        self.cache.delete("KEY1")
        self.cache.set("KEY1", "INITIAL")
        result = self.cache.add("KEY1", "NEW")

        self.assertEqual(self.cache.get("KEY1"), "INITIAL")
        self.assertFalse(result)
