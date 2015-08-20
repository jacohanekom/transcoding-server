import os, sys
import config
import time
import shutil
import requests
import tvdb_api
import threading
import tempfile

class publishThread(threading.Thread):

    def get_series_destination(self, show):
        t = tvdb_api.Tvdb(actors=True)
        title = t[show.metadata.show][show.metadata.season][show.metadata.episode]['episodename']

        if show.metadata.double_episode == 0:
           output = "{show} - S{season}E{episode} - {showname}{ext}".format(
             show = show.metadata.show, season = str(show.metadata.season).zfill(2),
             episode = str(show.metadata.episode).zfill(2), showname = title,
             ext = config.HANDBRAKE_EXTENSION
           )
        else:
           output = "{show} - S{season}E{episode}-E{episode1} - {showname}{ext}".format(
             show = show.metadata.show, season = str(show.metadata.season).zfill(2),
             episode = str(show.metadata.episode).zfill(2), showname = title,
             episode1 = str(show.metadata.episode+1).zfill(2),
             ext = config.HANDBRAKE_EXTENSION
           )

        return [os.path.join(self.__get_drive_mount__(show.metadata.show),
            config.PUBLISH_TVSHOWS_FOLDER, show.metadata.show, 'Season ' + str(show.metadata.season).zfill(2)), output]

    def get_movies_path(self, movie):
        path = "{name} ({year}){ext}".format(name=movie.metadata.name, year=movie.metadata.year,
                                              ext=config.HANDBRAKE_EXTENSION)

        return [os.path.join(self.__get_drive_mount__(movie.metadata.name), config.PUBLISH_MOVIES_FOLDER), path]

    def __get_drive_mount__(self, name):
        for (key, value,) in config.PUBLISH_MOUNTS.iteritems():
            lowerbound = int(value.split('-')[0])
            upperbound = int(value.split('-')[1])
            if ord(name[0:1].upper()) >= lowerbound and ord(name[0:1].upper()) <= upperbound:
                return key

        return tempfile.gettempdir()

    def trigger_sickbeard_refresh(self, show):
        t = tvdb_api.Tvdb()
        if config.SICKBEARD_HTTP_FOLDER:
            url = 'http://{host}:{port}/{http_folder}/api/{api_key}/?cmd=show.refresh&tvdbid={show}'
        else:
            url = 'http://{host}:{port}/api/{api_key}/?cmd=show.refresh&tvdbid={show}'
        requests.get(url.format(host=config.SICKBEARD_HOST, port=config.SICKBEARD_PORT, http_folder=config.SICKBEARD_HTTP_FOLDER, api_key=config.SICKBEARD_API_KEY, show=t[show]))

    def trigger_couchpotato_refresh(self):
        if config.COUCHPOTATO_HTTP_FOLDER:
            url = 'http://{host}:{port}/{http_folder}/api/{api_key}/manage.update/'
        else:
            url = 'http://{host}:{port}/api/{api_key}/manage.update/'
        requests.get(url.format(host=config.COUCHPOTATO_HOST, port=config.COUCHPOTATO_PORT, http_folder=config.COUCHPOTATO_HTTP_FOLDER, api_key=config.COUCHPOTATO_API_KEY))

    def updateStorage(self, uuid, obj):
        self.registered_files[uuid] = obj

    def getStorage(self, uuid):
        return self.registered_files[uuid]

    def getAvailableFiles(self):
        to_be_processed = list()
        for uuid in self.registered_files:
            if self.registered_files[uuid].status.state == 'Publish - Queued':
                to_be_processed.append(uuid)

        return to_be_processed

    def __init__(self, registered_files):
        threading.Thread.__init__(self)
        self.registered_files = registered_files

    def run(self):
        print 'Starting ' + self.name
        while True:
            for uuid in self.getAvailableFiles():
                file = self.getStorage(uuid)
                try:
                    converted_file = os.path.join(tempfile.gettempdir(), uuid + config.HANDBRAKE_EXTENSION)
                    file.status.state = 'Publish - Running'
                    self.updateStorage(uuid, file)

                    if file.metadata.type == 'tv':
                        destination = self.get_series_destination(file)

                        if not os.path.isdir(destination[0]):
                            os.makedirs(destination[0])

                        if os.path.isfile(os.path.join(destination[0], destination[1])):
                            raise Exception('File Already exist')
                        else:
                            shutil.copy2(converted_file, os.path.join(destination[0], destination[1]))
                        os.remove(converted_file)
                        os.remove(file.file)

                        if config.SICKBEARD_ENABLED:
                            self.trigger_sickbeard_refresh(file.metadata.show)
                    elif file.metadata.type == 'movie':
                        destination = self.get_movies_path(file)

                        if not os.path.isdir(destination[0]):
                            os.makedirs(destination[0])

                        if os.path.isfile(os.path.join(destination[0], destination[1])):
                            raise Exception('File Already Exist')
                        else:
                            shutil.copy2(converted_file, os.path.join(destination[0], destination[1]))

                        os.remove(converted_file)
                        os.remove(file.file)

                        if config.COUCHPOTATO_ENABLED:
                            self.trigger_couchpotato_refresh()

                    file.status.state = 'Publish - Done'
                    self.updateStorage(uuid, file)
                except:
                    file.status.state = 'Publish - Error - {error}'.format(error=sys.exc_info()[0])
                    self.updateStorage(uuid, file)

            time.sleep(60)
