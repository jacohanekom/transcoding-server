__author__ = 'Jaco-Hanekom'
import threading


class Base(object):
    messages = ["Queued", "Processing", "Done", "Error"]
    registered_files = dict()

    def get_name(self):
        return "{name}".format(name=self.__class__.__name__)

    def state_text(self, state, detail=None):
        if detail:
            return "{cls}-{state}-{detail}".format(cls=self.get_name(), state=self.messages[state], detail = detail)
        else:
            return "{cls}-{state}".format(cls=self.get_name(), state=self.messages[state])

    def update_storage(self, uuid, obj):
        self.registered_files[uuid] = obj

    def get_storage(self, uuid=None):
        if uuid is not None:
            return self.registered_files[uuid]
        else:
            return self.registered_files.keys()

    def get_available_files(self):
        to_be_processed = list()

        for uuid in self.registered_files:
            if hasattr(self.registered_files[uuid], "status"):
                if self.registered_files[uuid].status.state == self.get_name() + '-' + self.messages[0]:
                    to_be_processed.append(uuid)

        return to_be_processed

    def get_config(self):
        return self.config

    def __init__(self, registered_files, config):
        self.registered_files = registered_files
        self.config = config