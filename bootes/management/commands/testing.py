import time

from django.conf import settings
from django.core.cache import cache
from django.core.management import BaseCommand

from bootes.tasks import Service1Task, Service2Task, Service3Task


class Command(BaseCommand):
    help = 'Displays current time'

    def flush(self):
        for i in range(0, settings.TESTING_ROUNDS_COUNT):
            cache.delete(Service1Task.THE_NAME + "_{}".format(i))
            cache.delete(Service2Task.THE_NAME + "_{}".format(i))
            cache.delete(Service3Task.THE_NAME + "_{}".format(i))

    def feed(self, *args, **kwargs):
        for i in range(settings.TESTING_ROUNDS_COUNT):
            Service1Task().delay(i)
            Service2Task().delay(i)
            # Service3Task().delay(i)

    def handle(self, *args, **kwargs):
        self.flush()
        self.feed()
        old_service1_count = 0
        old_service2_count = 0
        old_service3_count = 0
        first = True
        start = time.time()
        delta = 1
        service_1_rates = list()
        service_2_rates = list()
        service_3_rates = list()
        while True:
            t = time.time()
            time.sleep(delta)
            service1_count = 0
            service2_count = 0
            service3_count = 0
            for i in range(0, settings.TESTING_ROUNDS_COUNT):
                service1_count += int(cache.get(Service1Task.THE_NAME + "_{}".format(i), 0))
                service2_count += int(cache.get(Service2Task.THE_NAME + "_{}".format(i), 0))
                service3_count += int(cache.get(Service3Task.THE_NAME + "_{}".format(i), 0))
                if (service1_count or service2_count or service3_count) and first:
                    start = time.time()
                    first = False

            service1_rate = round((service1_count - old_service1_count) / (time.time() - t) * 60 / delta, 2)
            service2_rate = round((service2_count - old_service2_count) / (time.time() - t) * 60 / delta, 2)
            service3_rate = round((service3_count - old_service3_count) / (time.time() - t) * 60 / delta, 2)

            if service1_count - old_service1_count:
                service_1_rates.append(service1_rate)
            if service2_count - old_service2_count:
                service_2_rates.append(service2_rate)
            if service3_count - old_service3_count:
                service_3_rates.append(service3_rate)

            old_service1_count = service1_count
            old_service2_count = service2_count
            old_service3_count = service3_count

            msg = "\n".join([
                "============ PASSED TIME: {} ==============".format(time.time() - start),
                "Service 1 rate: {}  --- AVG rate: {} --- Count: {}".format(service1_rate,
                                                                            round(sum(service_1_rates) / (len(service_1_rates) or 1), 2),
                                                                            service1_count),
                "Service 2 rate: {}  --- AVG rate: {} --- Count: {}".format(service2_rate,
                                                                            round(sum(service_2_rates) / (len(service_2_rates) or 1), 2),
                                                                            service2_count),
                "Service 3 rate: {}  --- AVG rate: {} --- Count: {}".format(service3_rate,
                                                                            round(sum(service_3_rates) / (len(service_3_rates) or 1), 2),
                                                                            service3_count),
            ])
            print(msg)
            print("\n\n\n")
