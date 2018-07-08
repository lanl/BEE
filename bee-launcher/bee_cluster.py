# system

from threading import Thread, Event


class BeeTask(Thread):
    def __init__(self):
        Thread.__init__(self)

        # Output colors
        self.__output_color_list = ["magenta", "cyan", "blue", "green",
                                    "red", "grey", "yellow"]
        self.output_color = "cyan"
        self.error_color = "red"
        self.warning_color = "yellow"

        # Events for workflow
        self.__begin_event = Event()
        self.__end_event = Event()
        self.__event_list = []

    # Event/Trigger management
    @property
    def begin_event(self):
        return self.__begin_event

    @begin_event.setter
    def begin_event(self, flag):
        """
        If bool T then set internal flag,
        else clear internal flag
        :param flag: boolean value
        """
        if flag:
            self.__begin_event.set()
        else:
            self.__begin_event.clear()

    @property
    def end_event(self):
        return self.__end_event

    @end_event.setter
    def end_event(self, flag):
        """
        If bool T then set internal flag,
        else clear internal flag
        :param flag: boolean value
        """
        if flag:
            self.__end_event.set()
        else:
            self.__end_event.clear()

    @property
    def event_list(self):
        return self.__event_list

    @event_list.setter
    def event_list(self, new_event):
        """
        Append event to event_list
        :param new_event:
        """
        self.__event_list.append(new_event)
