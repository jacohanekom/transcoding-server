__author__ = 'Jaco-Hanekom'
import threading


class Thread(threading.Thread):
    messages = ["Queued", "Processing", "Done", "Error"]

    def get_name(self):
        return type(self).name

    def state_text(self, state, detail=None):
        if detail:
            return "{cls} - {state} - {detail}".format(cls=self.get_name(), state=self.messages[state], error = detail)
        else:
            return "{cls} - {state}".format(cls=self.get_name(), state=self.messages[state])

    def update_storage(self, uuid, obj):
        self.registered_files[uuid] = obj

    def get_storage(self, uuid):
        return self.registered_files[uuid]

    def get_available_files(self):
        to_be_processed = list()
        for uuid in self.registered_files:
            if self.registered_files[uuid].status.state == self.__class__ + ' - ' + self.messages[0]:
                to_be_processed.append(uuid)

        return to_be_processed

    def __init__(self, registered_files):
        threading.Thread.__init__(self)
        self.registered_files = registered_files

    def run(self):
        None