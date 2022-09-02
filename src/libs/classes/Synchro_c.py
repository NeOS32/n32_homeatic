import threading
import logging


class Synchro_c(object):
    '''A synchro primitive which:
      - warns when there is reetrancy (same thread)
      - TBE
      '''

    def __init__(self):
        self.local_storage = threading.local()
        self.local_storage.lock_level = 0  # not sure if that is not guaranteeed

        self.sem = threading.Semaphore()

    def acquire(self):
        if not getattr(self.local_storage, 'lock_level', 0):
            # first time seen
            self.sem.acquire()
            self.local_storage.lock_level = 1
        else:
            # We already taken, so just increment. Also, it means we're entering critical section multiple times from the same thread
            self.local_storage.lock_level += 1
            logging.warn(
                f"We're entering same critical section multiple times={self.local_storage.lock_level}")

    def release(self):
        if getattr(self.local_storage, 'lock_level', 0) < 1:
            raise Exception("Trying to release a released lock.")

        self.local_storage.lock_level -= 1

        if 0x0 == self.local_storage.lock_level:
            self.sem.release()

    def __exit__(self, type, value, traceback):
        self.release()

    # for context manager
    __enter__ = acquire
