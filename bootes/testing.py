
class Command(BaseCommand):
    help = 'Displays current time'

    def flush(self):
        for i in range(0, settings.THE_LEN):
            cache.delete(ServiceSlackTask.THE_NAME + "_{}".format(i))
            cache.delete(ServiceZoomTask.THE_NAME + "_{}".format(i))
            cache.delete(ServiceGSuiteTask.THE_NAME + "_{}".format(i))

    def feed(self, *args, **kwargs):
        for i in range(settings.THE_LEN):
            ServiceSlackTask().delay(i)
            ServiceZoomTask().delay(i)
            ServiceGSuiteTask().delay(i)

    def handle(self, *args, **kwargs):
        self.flush()
        old_slack_count = 0
        old_zoom_count = 0
        old_gsuite_count = 0
        t = time.time()
        first = True
        start = time.time()
        while True:
            slack_count = 0
            zoom_count = 0
            gsuite_count = 0
            for i in range(0, settings.THE_LEN):
                slack_count += int(cache.get(ServiceSlackTask.THE_NAME + "_{}".format(i), 0))
                zoom_count += int(cache.get(ServiceZoomTask.THE_NAME + "_{}".format(i), 0))
                gsuite_count += int(cache.get(ServiceGSuiteTask.THE_NAME + "_{}".format(i), 0))
                if (slack_count or zoom_count or gsuite_count) and first:
                    start = time.time()
                    first = False

            slack_rate = (slack_count - old_slack_count) / (time.time() - t)
            zoom_rate = (zoom_count - old_zoom_count) / (time.time() - t)
            gsuite_rate = (gsuite_count - old_gsuite_count) / (time.time() - t)

            old_slack_count = slack_count
            old_zoom_count = zoom_count
            old_gsuite_count = gsuite_count

            msg = "\n".join([
                "============ PASSED TIME: {} ==============".format(time.time() - start),
                "SLACK rate: {}  ---  Count: {}".format(slack_rate, slack_count),
                "ZOOM rate: {}  ---  Count: {}".format(zoom_rate, zoom_count),
                "G-Suite rate: {}  ---  Count: {}".format(gsuite_rate, gsuite_count),
            ])
            print(msg)
            print("\n\n\n")
            t = time.time()
            time.sleep(1)
