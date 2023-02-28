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

    def __init__(self, limit=(None, None), sliding=False, unit='m'):
        """
            Time limit is in minutes, if not unit is stated ['s', 'm', 'h']
        """
        self._tracker = {}
        self._count_limit = limit[0]
        self._interval = limit[1]
        self._sliding = sliding
        self._divide = 60.0
        if unit == 's':
            self._divide = 1.0
        elif unit == 'h':
            self._divide = 3600.0
        if self._interval is not None:
            self._interval /= self._divide

    def _interval_reached(self, info):
        """
            Returns true if it was more than
            self._interval time since the start
            of info's previous interval
        """
        if self._interval is None:
            return False
        return ((time.time() / self._divide) - self._tracker[info]['s']) > self._interval

    def _reset_count(self, info, count=0):
        self._tracker[info] = {
            's': time.time() / self._divide,
            'c': count
        }

    def _get_count(self, info):
        if info in self._tracker:
            return self._tracker[info]['c']
        return None

    def reset_all(self):
        """
            Resets count for all info stored
        """
        for info in self._tracker:
            self._reset_count(info)

    def wipe(self):
        """
            Removes all counting done
        """
        self._tracker = {}
        self._interval = None
        self._count_limit = None

    def _count_limit_reached(self, info):
        """
            Check if count limit is reached
        """
        if info not in self._tracker:
            return self._count_limit is not None or self._count_limit == 0
        return self._tracker[info]['c'] > self._count_limit

    def _in_window(self, time_point, current_time):
        """
            Checks if a time is in the current interval
            window
        """
        return (current_time - time_point) <= self._interval

    def _update_window(self, info):
        """
            Filters out values not in window
            and appends current time
        """
        if info not in self._tracker or 'w' not in self._tracker[info]:
            self._tracker[info] = {
                'w': [] 
            }
        # check window start
        window_start = 0
        current_time = time.time() / self._divide
        for i, time_point in enumerate(self._tracker[info]['w']):
            if self._in_window(time_point, current_time):
                window_start = i
                break
        self._tracker[info]['w'] = self._tracker[info]['w'][window_start:]
        # if size is not count limit, append
        length = len(self._tracker[info]['w'])
        if length < self._count_limit:
            self._tracker[info]['w'].append(current_time)
        return length+1

    def reached(self, info) -> bool:
        """
            Checks if info has reached its limit
            Returns true if it is ok
        """
        if self._count_limit is None:
            # Not valid if count limit is None
            return False
        # window check
        if self._sliding:
            new_length = self._update_window(info)
            return new_length > self._count_limit
        # count
        if info not in self._tracker or self._interval_reached(info):
            self._reset_count(info)
        self._tracker[info]['c'] += 1
        return self._count_limit_reached(info)
