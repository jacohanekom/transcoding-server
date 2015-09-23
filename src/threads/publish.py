import os, sys
import time
import ftplib
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

    def ftp_create_dir_recursively(self, ftp, directory):
        ftp.cwd("/")

        for dir in directory.split("/")[1:-1]:
            try:
                ftp.cwd(dir)
            except:
                ftp.mkd(dir)
                ftp.cwd(dir)

    def ftp_copy_files(self, source, destination, ftp=None):
        if ftp is None:
            ftp_host = super(PublishThread, self).get_config()['PUBLISH_FTP_HOST']
            ftp_username = super(PublishThread, self).get_config()['PUBLISH_USER_NAME']
            ftp_password = super(PublishThread, self).get_config()['PUBLISH_PASSWORD']

            ftp = ftplib.FTP(ftp_host, ftp_username, ftp_password)

        self.ftp_create_dir_recursively(ftp, directory=destination[0])
        ftp.cwd(destination[0])

        try:
            ftp.delete(destination[1])
        except:
            None

        ftp.storbinary('STOR {file}'.format(file=destination[1]), open(source, 'rb'))

    def run(self):
        print 'Starting ' + super(PublishThread, self).get_name()
        while True:
            for uuid in super(PublishThread, self).get_available_files():
                file = super(PublishThread, self).get_storage(uuid)
                try:
                    source_file = os.path.join(tempfile.gettempdir(), uuid +
                            super(PublishThread, self).get_config()['HANDBRAKE_EXTENSION'])

                    file.status.state = super(PublishThread, self).state_text(1)
                    super(PublishThread, self).update_storage(uuid, file)

                    if not self.__has_metadata__(super(PublishThread, self).get_config()['METADATA_ATOMIC_PARSLEY'],
                                                 source_file):
                        #try and download metadata again
                        file.status.state = super(PublishThread, self).state_text(4)
                        super(PublishThread, self).update_storage(uuid, file)
                    else :
                        destination = None
                        if file.metadata.type == 'tv':
                            destination = self.__get_series_destination__(file)
                        else:
                            destination = self.__get_movie_destination__(file)

                        self.ftp_copy_files(source_file, destination)
                        os.remove(source_file)
                        os.remove(file.file)

                        file.status.state = super(PublishThread, self).state_text(2)
                        super(PublishThread, self).update_storage(uuid, file)
                except:
                    file.status.state = super(PublishThread, self).state_text(3, traceback.format_exc())
                    super(PublishThread, self).update_storage(uuid, file)

            time.sleep(60)