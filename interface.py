import uuid, os, config
from guessit import PY2, u, guess_file_info
import tmdbsimple as tmdb
import tvdb_api

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

    def get_show_details(self, path):
        result = {}
        guess = guess_file_info(path, info='filename')

        if guess['type'] == "episode":
            try:
                result["type"] = "tv"
                result["show"] = guess["series"]
                result["season"] = guess["season"]
                result["episode"] = guess["episodeNumber"]

                if result.has_key("episodeList"):
                    result["double_episode"] = 1
                else:
                    result["double_episode"] = 0

                t = tvdb_api.Tvdb()
                if t[result["show"]][result["season"]][result["episode"]]["episodename"] is None:
                    return []
                else:
                    return result
            except:
                return []
        elif guess['type'] == "movie":
            try:
                result["type"] = "movie"
                result["name"] = guess["title"]
                result["year"] = guess["year"]

                search = tmdb.Search()
                search.movie(query=result["name"])
                i = 0
                for s in search.results:
                    if int(s['release_date'][0:4]) == int(result["year"]):
                        i+=1

                if i > 0:
                    return result
                else:
                    return []
            except:
                return []

        return []

    def is_file_supported(self, file):
        filename, file_extension = os.path.splitext(file)

        for ext in config.HANDBRAKE_SUPPORTED_FILES:
            if file_extension.lower() == ext:
                return True

        return False