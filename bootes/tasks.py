from abc import ABCMeta, abstractmethod

from celery import Task

from bootes.helpers import DistributedLock


class RegisterMetaclass(ABCMeta):

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ignorable = getattr(cls, "_{name}{var}".format(name=cls.__name__, var="__ignore"), False)
        if not ignorable:
            obj = cls()
            app.register_task(obj)


class BaseTask(Task, metaclass=RegisterMetaclass):
    """
    Base task class for creating tasks.
    """

    # To make Celery not register this task.
    __ignore = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = self.__class__.__name__


class UpdateService(BaseTask):
    # max_retries = 100

    # To make Celery not register this task.
    __ignore = True

    @transaction.atomic
    def run(self, email_address):

        if self.request.retries > 0:
            return self._run(email_address)

        with DistributedLock(self.THE_NAME, self.THE_RATE_LIMIT) as lock:
            countdown = lock.notify_start()
            return self.retry(countdown=countdown)

    def _run(self, email_address):
        self.testing(email_address)
        cache.set(self.THE_NAME + "_{}".format(email_address), 1)

    @abstractmethod
    def testing(self, workday_service):
        raise NotImplementedError()


class Service1Task(UpdateService):
    THE_NAME = "Service 1"
    THE_RATE_LIMIT = 100  # per minute

    def testing(self, workday_service):
        a = 9  # ** 3 ** 9
        a += 1
        return a


class Service2Task(UpdateService):
    THE_NAME = "Service 2"
    THE_RATE_LIMIT = 50  # per minute

    def testing(self, workday_service):
        a = 9  # ** 3 ** 8
        a += 1
        return a


class Service3Task(UpdateService):
    THE_NAME = "Service 3"
    THE_RATE_LIMIT = 200  # per minute

    def testing(self, workday_service):
        a = 9  # ** 3
        a += 1
        return a
