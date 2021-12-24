import time

from core.cache import MemcachedCache
from core.nekkar import Bootes

cache = MemcachedCache("localhost", 11211)
rate_limit = Bootes(cache=cache)


class TestingAPIServiceMock:

    @property
    def _user_data(self):
        return {
            "id": "1",
            "name": "John Doe",
            "email": "John.Doe@localhost.local"
        }

    @rate_limit("get_users", 200)
    def get_users(self) -> list:
        time.sleep(0.3)
        return [self._user_data]

    @rate_limit("get_user", 200)
    def get_user(self) -> dict:
        time.sleep(0.2)
        return self._user_data


def main():
    pass


if __name__ == "__main__":
    main()
