import os, sys
import config
import time
import shutil
import tempfile
import utils

class PublishThread(utils.Thread):
    def __get_tv_show_destination__(self, show):
        if show.metadata.double_episode == 0:
           output = "{show} - S{season}E{episode} - {showname}{ext}".format(
             show = show.metadata.show, season = str(show.metadata.season).zfill(2),
             episode = str(show.metadata.episode).zfill(2), showname = show.metadata.title.replace("/",""),
             ext = config.HANDBRAKE_EXTENSION
           )
        else:
           output = "{show} - S{season}E{episode}-E{episode1} - {showname}{ext}".format(
             show = show.metadata.show, season = str(show.metadata.season).zfill(2),
             episode = str(show.metadata.episode).zfill(2), showname = show.metadata.title.replace("/",""),
             episode1 = str(show.metadata.episode+1).zfill(2),
             ext = config.HANDBRAKE_EXTENSION
           )

        return [os.path.join(self.__get_drive_mount__(show.metadata.show),
            config.PUBLISH_TVSHOWS_FOLDER, show.metadata.show, 'Season ' + str(show.metadata.season).zfill(2)), output]

    def __get_movie_destination__(self, movie):
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

    def run(self):
        print 'Starting ' + super(PublishThread, self).get_name()
        while True:
            for uuid in super(PublishThread, self).get_available_files():
                file = super(PublishThread, self).get_storage(uuid)
                try:
                    converted_file = os.path.join(tempfile.gettempdir(), uuid + config.HANDBRAKE_EXTENSION)
                    file.status.state = self.state_text(1)
                    super(PublishThread, self).updateStorage(uuid, file)

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

                    file.status.state = super(PublishThread, self).state_text(2)
                    super(PublishThread, self).update_storage(uuid, file)
                except:
                    file.status.state = super(PublishThread, self).state_text(3, error=sys.exc_info()[0])
                    super(PublishThread, self).update_storage(uuid, file)

            time.sleep(60)
