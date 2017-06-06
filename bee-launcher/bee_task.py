from threading import Thread
class BeeTask(Thread):
    def __init__(self):
        Thread.__init__(self)
    
    def get_begin_event(self):
        pass

    def get_end_event(self):
        pass

    def add_wait_event(self, new_event):
        pass
