"""
    Limiter class for Logger,
    purpose is to rate-limit messages or
    simply just allow the n first messages.
"""
import time

class Limiter:
    """
        A class for tracking information sent
    """

    def __init__(self, limit=None, interval=(None, 's'), sliding=False, message=None):
        """
            Time limit is in minutes.
            Interval is (time [int], unit [s, m, h]) or int for seconds,
            where default is unit in seconds.
            sliding sets if the window should be sliding
        """
        self.__tracker = {}
        self.__limit = limit
        self.__interval = None
        self.__sliding = sliding
        self._message = message
        self.__first_reach = False
        # Default is seconds
        self.__divide = 1.0
        if isinstance(interval, tuple):
            if len(interval) > 0:
                self.__interval = interval[0]
            if len(interval) > 1:
                unit = interval[1]
                if unit == 'm':
                    self.__divide = 60.0
                elif unit == 'h':
                    self.__divide = 3600.0
        if type(interval) in [float, int]:
            self.__interval = float(interval)

    def __interval_reached(self, info):
        """
            Returns true if it was more than
            self._interval time since the start
            of info's previous interval
        """
        if self.__interval is None:
            return False
        return ((time.time() - self.__tracker[info]['s'])/self.__divide) > self.__interval

    def __reset_count(self, info, count=0):
        self.__tracker[info] = {
            's': time.time(),
            'c': count
        }

    def wipe(self):
        """
            Wipes the tracker
        """
        self.__tracker = {}

    def __limit_reached(self, info):
        """
            Check if count limit is reached
        """
        return self.__tracker[info]['c'] > self.__limit

    def __in_window(self, time_point, current_time):
        """
            Checks if a time is in the current interval
            window
        """
        return (current_time - time_point) <= self.__interval

    def __update_first_reach(self, count):
        self.__first_reach = (count > self.__limit) and not self.__first_reach

    def __update_window(self, info):
        """
            Filters out values not in window
            and appends current time
        """
        if info not in self.__tracker or 'w' not in self.__tracker[info]:
            self.__tracker[info] = {
                'w': [] 
            }
        # check window start
        window_start = 0
        current_time = time.time()
        for i, time_point in enumerate(self.__tracker[info]['w']):
            if self.__in_window(time_point, current_time):
                window_start = i
                break
        self.__tracker[info]['w'] = self.__tracker[info]['w'][window_start:]
        # if size is not count limit, append
        length = len(self.__tracker[info]['w'])
        if length < self.__limit:
            self.__tracker[info]['w'].append(current_time)
        return length+1

    def reached(self, info) -> bool:
        """
            Checks if info has reached its limit
            Returns true if it is ok
        """
        if self.__limit is None:
            # Not valid if count limit is None
            return False
        # window check
        if self.__sliding:
            new_length = self.__update_window(info)
            self.__update_first_reach(new_length)
            return new_length > self.__limit
        # count
        if info not in self.__tracker or self.__interval_reached(info):
            self.__reset_count(info)
        self.__tracker[info]['c'] += 1
        self.__update_first_reach(self.__tracker[info]['c'])
        return self.__limit_reached(info)

    def get_overflow_message(self):
        """
            Returns overflow message
        """
        if self.__first_reach:
            return self._message
        return None
