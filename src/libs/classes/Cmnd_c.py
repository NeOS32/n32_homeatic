import threading
import logging
import time

THREAD_JOIN_TIMEOUT = 5


def wrapper_for_closing(*args):
    cmd = args[0]

    if cmd.get_fun():
        if True == (cmd.get_fun())(cmd):  # is finished?
            cmd.stop_action()


def local_wrapper(*args):
    cmd = args[0]

    # it False, it means probably call count is reached, so giving up
    if False == cmd.do_restart():
        cmd.restart_counting()


def wrapper(*args):
    cmnd = args[0]

    if cmnd.is_last_run():
        cmnd.reset()
    else:
        cmnd.do_next_call()


class Cmnd_c:  # singletone
    __instance = None
    __sample_id = None
    __fun = None
    __repeat_time_in_s = None
    __call_count = 0
    __curent_call_count = 0
    __timer_id = None
    __is_cancelled = False
    __do_retrigger = False
    __thread_id = None
    __remained_calls = None

    # _persist_methods = ['get', 'save', 'delete', 'asdf']

    def __init__(self, sample_id, fun, repeat_time_in_s, call_count):
        '''default constructor

        Args:
            sample_id (int): the DB's id of sample being played
            fun (): function to be called
            repeat_time_in_s (int): repeat time in seconds
            call_count (int): how many time this function should be called before expiration?

        Raises:
            RuntimeError: none at the moment

        Returns:
            nothing since it's a constructor
        '''
        self.__sample_id = sample_id
        self.__fun = fun
        self.__repeat_time_in_s = repeat_time_in_s
        self.__call_count = call_count
        self.restart_counting()

    def add_action(self, value):
        pass

    def get_fun(self):
        return wrapper

    def get_arg_fun(self):
        return self.__fun

    def restart_counting(self):
        self.__curent_call_count = 0x0

    def is_first_time(self):
        return 0x0 == self.__curent_call_count

    def get_sample_id(self):
        return self.__sample_id

    def get_repeat_interval(self):
        return self.__repeat_time_in_s

    def get_name(self):
        return f'Command #{self.__sample_id}'

    def get_interval(self):
        return self.repeat_time_in_s

    def reset(self):
        self.stop_action()
        self.restart_counting()

    def stop_action(self):
        if self.__timer_id:
            self.__timer_id.cancel()
            # self.__timer_id.join(THREAD_JOIN_TIMEOUT)
            if self.__timer_id.is_alive():
                logging.error(f"ERR: thread is still alive!")
            self.__timer_id = None
        else:
            logging.warning(
                f"WARN: couldn't stop action since timer din't existed")

    def do_restart(self):
        if False == self.is_last_run():
            logging.debug(
                f"Doing restart before it's actually needed")

        # restart
        self.restart_counting()

        return self.do_next_call()

    def do_next_call(self):
        if self.__timer_id:
            self.stop_action()

        # interval, function, args=None, kwargs=None
        self.__timer_id = threading.Timer(
            self.__repeat_time_in_s, self.get_fun(), [self])
        if self.__timer_id:
            self.__timer_id.name = self.get_name()
            self.__curent_call_count += 1
            self.__timer_id.start()
            return True  # success
        else:
            logging.error(f"ERR: can't start the timer!")
        return False  # failure

    #####################

    def is_last_run(self):
        return 0 == self.__remained_calls

    def is_still_running(self):
        if not self.__thread_id:
            return False

        assert(self.__thread_id)
        return self.__thread_id.is_alive()

    def thread_loop(self):
        self.__remained_calls = self.__call_count

        while self.__remained_calls > 0 and False == self.__is_cancelled:
            (self.__fun)(self)

            time.sleep(self.__repeat_time_in_s)
            self.__remained_calls -= 1

            # when an user asked for retrigger in the background
            if self.__do_retrigger:
                self.__do_retrigger = False
                self.__remained_calls = self.__call_count

        self.__thread_id = None
        self.__is_cancelled = False
        self.__do_retrigger = False

    # start commands loop
    def trigger(self):
        assert(False == self.is_still_running())

        self.__thread_id = threading.Thread(
            target=Cmnd_c.thread_loop, args=(self,))
        self.__thread_id.start()

    # used when a command is running, but we want to start it again from with initial conditions
    def retrigger(self):
        self.__do_retrigger = True
        self.__is_cancelled = False

    def cancel_unblocking(self):
        self.__is_cancelled = True

    def cancel_blocking(self):
        self.__is_cancelled = True
        self.__thread_id.join()
