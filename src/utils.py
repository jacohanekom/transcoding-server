__author__ = 'Jaco-Hanekom'
import threading

class Thread(threading.Thread):
    queue = []

    def update_storage(self, uuid, obj):
        self.registered_files[uuid] = obj

    def get_storage(self, uuid):
        return self.registered_files[uuid]

    def get_available_files(self):
        to_be_processed = list()
        for uuid in self.registered_files:
            if self.registered_files[uuid].status.state == 'Transcoding - Queued':
                to_be_processed.append(uuid)

        return to_be_processed

    def __init__(self, registered_files):
        threading.Thread.__init__(self)
        self.registered_files = registered_files

    def run(self):
        None