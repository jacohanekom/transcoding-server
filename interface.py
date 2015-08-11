import uuid

class rpcInterface(object):
    def __init__(self, registered_files):
        self.registered_files = registered_files

    def add_movie(self, file, name, year):
        for already_present in self.registered_files:
            if self.registered_files[already_present].file == file:
                raise Exception('File Already present')

        instruction = type('movie', (), {})()
        setattr(instruction, 'file', file)
        metadata = type('metadata', (), {})()
        setattr(metadata, 'name', name)
        setattr(metadata, 'year', year)
        setattr(metadata, 'type', 'movie')
        status = type('status', (), {})()
        setattr(status, 'state', 'queued')
        setattr(status, 'percent', '0')
        setattr(status, 'time', '0')
        setattr(status, 'fps', '0')
        setattr(instruction, 'metadata', metadata)
        setattr(instruction, 'status', status)
        id = str(uuid.uuid4())
        self.registered_files[id] = instruction
        return id

    def add_tv_show(self, file, show, season, episode, double_episode):
        for already_present in self.registered_files:
            if self.registered_files[already_present].file == file:
                raise Exception('File Already present')

        instruction = type('movie', (), {})()
        setattr(instruction, 'file', file)

        metadata = type('metadata', (), {})()
        setattr(metadata, 'show', show)
        setattr(metadata, 'season', season)
        setattr(metadata, 'episode', episode)
        setattr(metadata, 'double_episode', double_episode)
        setattr(metadata, 'type', 'tv')

        status = type('status', (), {})()

        setattr(status, 'state', 'queued')
        setattr(status, 'percent', '0')
        setattr(status, 'time', '0')
        setattr(status, 'fps', '0')
        setattr(instruction, 'metadata', metadata)
        setattr(instruction, 'status', status)

        id = str(uuid.uuid4())
        self.registered_files[id] = instruction
        return id

    def get_registered_shows(self):
        return self.registered_files.keys()

    def get_details(self, uuid):
        return self.registered_files[uuid]