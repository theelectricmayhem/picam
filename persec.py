# Class for counting events per second

import datetime


class PerSec:
    def __init__(self, name):
        self.init_time = datetime.datetime.now()
        self.last_update = 0
        self.elapsed_timedelta = datetime.timedelta(seconds=0)
        self.event_counter = 0
        self.name = name
        return

    def update(self):
        now = datetime.datetime.now()
        self.elapsed_timedelta = now - self.init_time
        self.last_update = now
        self.event_counter = self.event_counter + 1

    def report(self):
        print(self.name, ":",
              "\n\t", "Init: ", self.init_time,
              "\n\t", "last_update: ", self.last_update,
              "\n\t", "elapsed: ", self.elapsed_timedelta,
              "\n\t", "total events: ", self.event_counter)
        if self.elapsed_timedelta.seconds == 0:
            print("\t", "events per second: N/A")
        else:
            print("\t", "events per second: ", self.event_counter / self.elapsed_timedelta.seconds)
        if self.event_counter == 0:
            print("\t", "cycle time: N/A")
        else:
            print("\t", "cycle time: ", self.elapsed_timedelta.seconds / self.event_counter)

    def __del__(self):
        self.report()
        return
