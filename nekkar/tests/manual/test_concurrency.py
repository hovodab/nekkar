import os
import time
from multiprocessing import Process
from threading import Thread

from nekkar.core.cache import MemcachedCache
from nekkar.core.limiter import Nekkar
from nekkar.tests.manual.report import main as report_main


cache = MemcachedCache("localhost", 11211)
rate_limit = Nekkar(cache=cache, auto_race_condition_resistance=True)


def logg_time(name):
    filename = f"{name}.log"
    with open(filename, "a+") as f:
        f.write(str(time.time() * 1000) + "\n")
    time.sleep(0.5)


def handle(method):
    for i in range(20):
        method(i)


def wrap_one(i):
    @rate_limit("executable1", 200)
    def source(index):
        now = time.time()
        print(f"{i} | {index} -+--------------- {now}")
        logg_time(f"executable{i}")
        return i
    return source


def generate_sources(count):
    sources = list()
    for i in range(1, 1 + count):
        source = wrap_one(i)
        sources.append(source)
    return sources


def wrapp(method, *args, **kwargs):
    def wrapper():
        return method(*args, **kwargs)
    return wrapper


def main(number_of_sources, process=True):
    logs = [f"executable{i}.log" for i in range(1, 1 + number_of_sources)]
    for log in logs:
        if os.path.exists(log):
            os.remove(log)

    methods = generate_sources(number_of_sources)

    handler_cls = Process if process else Thread

    handlers = list()
    for method in methods:
        handler = handler_cls(target=wrapp(handle, method))
        handlers.append(handler)

    for handler in handlers:
        handler.start()

    for handler in handlers:
        handler.join()


if __name__ == "__main__":
    number_of_sources = 2
    main(number_of_sources)
    report_main(number_of_sources)
