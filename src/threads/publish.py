import os, sys
import time
import shutil
import tempfile
import utils
import subprocess, traceback

class PublishThread(utils.Base):
    def __get_series_destination__(self, show):
        if show.metadata.double_episode == 0:
           output = "{show} - S{season}E{episode} - {showname}{ext}".format(
             show = show.metadata.show, season = str(show.metadata.season).zfill(2),
             episode = str(show.metadata.episode).zfill(2), showname = show.metadata.title,
             ext = super(PublishThread, self).get_config()['HANDBRAKE_EXTENSION']
           )
        else:
           output = "{show} - S{season}E{episode}-E{episode1} - {showname}{ext}".format(
             show = show.metadata.show, season = str(show.metadata.season).zfill(2),
             episode = str(show.metadata.episode).zfill(2), showname = show.metadata.title,
             episode1 = str(show.metadata.episode+1).zfill(2),
             ext = super(PublishThread, self).get_config()['HANDBRAKE_EXTENSION']
           )

        return [os.path.join(self.__get_drive_mount__(show.metadata.show),
            super(PublishThread, self).get_config()['PUBLISH_TVSHOWS_FOLDER'],
            show.metadata.show, 'Season ' + str(show.metadata.season).zfill(2)), output]

    def __get_movie_destination__(self, movie):
        path = "{name} ({year}){ext}".format(name=movie.metadata.name, year=movie.metadata.year,
                                              ext=super(PublishThread, self).get_config()['HANDBRAKE_EXTENSION'])

        return [os.path.join(self.__get_drive_mount__(movie.metadata.name), super(PublishThread, self)
                             .get_config()['PUBLISH_MOVIES_FOLDER']), path]

    def __get_drive_mount__(self, name):
        for (key, value,) in super(PublishThread, self).get_config()['PUBLISH_MOUNTS'].iteritems():
            lowerbound = int(value.split('-')[0])
            upperbound = int(value.split('-')[1])
            if ord(name[0:1].upper()) >= lowerbound and ord(name[0:1].upper()) <= upperbound:
                return key

        return tempfile.gettempdir()

    def __has_metadata__(self, atomic_parsley_path, file):
        cmd = [atomic_parsley_path, file, '-t']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        content = ""

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        while True:
            out = proc.stdout.readline()
            content += repr(out)

            if out == '':
                break

        if content.count("Atom") < 2:
            return False
        else:
            return True

    def run(self):
        print 'Starting ' + super(PublishThread, self).get_name()
        while True:
            for uuid in super(PublishThread, self).get_available_files():
                file = super(PublishThread, self).get_storage(uuid)
                try:
                    converted_file = os.path.join(tempfile.gettempdir(), uuid +
                                                  super(PublishThread, self).get_config()['HANDBRAKE_EXTENSION'])

                    file.status.state = super(PublishThread, self).state_text(1)
                    super(PublishThread, self).update_storage(uuid, file)
                    destination = None

                    if not self.__has_metadata__(super(PublishThread, self).get_config()['METADATA_ATOMIC_PARSLEY'], converted_file):
                        #try and download metadata again
                        file.status.state = super(PublishThread, self).state_text(4)
                        super(PublishThread, self).update_storage(uuid, file)
                    else :
                        if file.metadata.type == 'tv':
                            destination = self.__get_series_destination__(file)

                            if not os.path.isdir(destination[0]):
                                os.makedirs(destination[0])

                            if os.path.isfile(os.path.join(destination[0], destination[1])):
                                os.remove(os.path.join(destination[0], destination[1]))

                            result = os.system("cp '%s' '%s'" % (converted_file, (os.path.join(destination[0], destination[1]))))
                            if result != 0:
                                raise Exception("Unable to copy file")

                            os.remove(converted_file)
                            os.remove(file.file)
                        elif file.metadata.type == 'movie':
                            destination = self.__get_movie_destination__(file)

                            if not os.path.isdir(destination[0]):
                                os.makedirs(destination[0])

                            if os.path.isfile(os.path.join(destination[0], destination[1])):
                                os.remove(os.path.join(destination[0], destination[1]))

                            result = os.system("cp '%s' '%s'" % (converted_file, (os.path.join(destination[0], destination[1]))))
                            if result != 0:
                                raise Exception("Unable to copy file")

                            os.remove(converted_file)
                            os.remove(file.file)

                        if destination:
                            setattr(file, "destination", destination)

                        file.status.state = super(PublishThread, self).state_text(2)
                        super(PublishThread, self).update_storage(uuid, file)
                except:
                    file.status.state = super(PublishThread, self).state_text(3, traceback.format_exc())
                    super(PublishThread, self).update_storage(uuid, file)

            time.sleep(60)