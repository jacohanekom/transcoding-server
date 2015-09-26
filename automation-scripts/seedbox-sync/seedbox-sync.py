#!/usr/bin/env python

import xmlrpclib, paramiko, os, tempfile, uuid, json, time, datetime, fnmatch, threading, sys, socket
import logging
import operator
from guessit import PY2, u, guess_file_info
import tvdb_api

class ruTorrent():
    def __init__(self, rTorrentURL, rTorrentUsername, rTorrentPassword, wwwUser):
        url = ("http://{username}:{password}@{host}/{www_user}/rutorrent/plugins/httprpc/action.php".format(
                                                                    username=rTorrentUsername,
                                                                    password=rTorrentPassword,
                                                                    host=rTorrentURL,
                                                                    www_user=wwwUser))
        self.proxy = xmlrpclib.ServerProxy(url)

    def get_torrent_indicators(self):
        torrents = []

        multicall = xmlrpclib.MultiCall(self.proxy)
        multicall.d.multicall("main", "d.get_hash=")
        results = multicall()

        for result in tuple(results)[0]:
            torrents.append(result[0])

        return torrents

    def remove_torrent(self, info_hash):
        self.proxy.d.try_stop(info_hash)
        self.proxy.d.erase(info_hash)

    def get_file_lists(self, info_hash):
        counter = 0
        files = []

        while True:
            try:
                files.append(self.proxy.f.get_frozen_path(info_hash,counter))
                counter+=1
            except xmlrpclib.Fault:
                break

        return files

    def is_torrent_seeding(self, info_hash):
        if self.proxy.d.get_complete(info_hash) == 0:
            return False
        else:
            return True

    def torrent_user(self, info_hash):
        return self.proxy.d.get_base_path(info_hash).replace('/home/jhanekom/data/','').split("/")[0]

class remoteIO():
    def __init__(self, host, username, password):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username, password=password)

        transport = paramiko.Transport((host, 22))
        transport.connect(username=username, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(transport)

        self.host = host
        self.username = username
        self.password = password

    def check_connection(self):
        try:
            self.ssh.exec_command('ls')
        except socket.error as e:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, username=self.username, password=self.password)

            transport = paramiko.Transport((self.host, 22))
            transport.connect(username=self.username, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(transport)

    def close(self):
        self.ssh.close()
        self.sftp.close()

    def copy_files(self, source, destination):
        self.ssh.exec_command('mkdir -p "{directory}"'.format(directory=os.path.dirname(destination)))
        self.ssh.exec_command('cp "{source}" "{destination}"'.format(source=source, destination=destination))

    def __merge_two_dicts__(self, x, y):
        '''Given two dicts, merge them into a new dict as a shallow copy.'''
        z = x.copy()
        z.update(y)
        return z

    def get_file_list(self, path):
        file_list = {}

        for dir in self.sftp.listdir(path=path):
            if int(oct(self.sftp.stat(os.path.join(path, dir)).st_mode)[0:2]) == 4:
                file_list = self.__merge_two_dicts__(file_list, self.get_file_list(os.path.join(path, dir)))
            else:
                utime = self.sftp.stat(os.path.join(path, dir)).st_mtime
                last_modified = datetime.datetime.fromtimestamp(utime)

                file_list[os.path.join(path, dir)] = last_modified

        return file_list

    def delete_files(self, path):
        self.sftp.remove(path)

    def get_http_url(self, path, wwwUser):
        return path.replace("/home/{user}".format(user=self.username), "http://{user}:{password}@{server}/{www_user}".format(
            user = self.username, password=self.password, server=self.host, www_user=wwwUser))

    def remote_unrar(self, from_path, to_path):
        rar_files = []
        self.ssh.exec_command('mkdir -p "{directory}"'.format(directory=to_path))

        command = "unrar e -y '{path}' '{to_path}'".format(path=from_path, to_path=to_path)
        (stdin, stdout, stderr) = self.ssh.exec_command(command)
        output = ""
        while True:
            output += stdout.read(1)

            if "All OK" in output :
                for row in output.split("Extracting from"):
                    if 'UNRAR' not in row:
                        rar_files.append(row.split("\n")[0])

                return rar_files
            elif "Total errors" in output:
                return []

    def write_index_file(self, files, wwwUser):
        with open(os.path.join(tempfile.gettempdir(), str(uuid.uuid4())), 'a') as file:
            file.write(json.dumps(files))

        self.sftp.put(file.name, '/home/{username}/.{user}.index.json'.format(username=rTorrentUsername,user=wwwUser))
        os.remove(file.name)

    def get_index_file(self, wwwUser):
        data = {}
        try:
            temp = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            self.sftp.get('/home/{username}/.{user}.index.json'.format(username=rTorrentUsername,user=wwwUser), temp)

            with open(temp) as json_file:
                data = json.load(json_file)

            os.remove(temp)
        finally:
            return data

class aria(object):
    def __init__(self, host, port):
        self.aria2 = xmlrpclib.ServerProxy('http://{host}:{port}/rpc'.format(host=host, port=port))

    def is_download_done(self, gid):
        return self.aria2.aria2.tellStatus(gid)['status'] == "complete"

    def is_download_in_progress(self, gid):
        return \
            self.aria2.aria2.tellStatus(gid)['status'] == "waiting" or \
            self.aria2.aria2.tellStatus(gid)['status'] == "active" or \
            self.aria2.aria2.tellStatus(gid)['status'] == "paused"

    def is_download_error(self, gid):
        return self.aria2.aria2.tellStatus(gid)['status'] == "error" or \
            self.aria2.aria2.tellStatus(gid)['status'] == "removed"

    def register_download(self, source_url, destination_dir):
        return self.aria2.aria2.addUri([source_url,], dict(dir=destination_dir))

    def get_destination_files(self, gid):
        return self.aria2.aria2.getFiles(gid)[0]['path']

    def purge_download(self, gid):
        self.aria2.aria2.removeDownloadResult(gid)


class Seedbox (threading.Thread):
    def __init__(self, logger, remoteIO):
        threading.Thread.__init__(self)
        self.logger = logger
        self.remoteIO = remoteIO

    def copy_torrent(self, remote_interface, torrent_interface, torrent):
        files = torrent_interface.get_file_lists(torrent)
        files_to_ignore = []

        for file in files:
            if file.endswith("rar"):
                self.logger.info("Unzipping file - {file}".format(file = file))
                path = os.path.dirname(file).replace("/home/{rUser}/data/{user}/torrents".format(rUser=rTorrentUsername,user=rUser),
                                          "/home/{rUser}/data/{user}/watch".format(rUser=rTorrentUsername, user=rUser))
                files_to_ignore = remote_interface.remote_unrar(file, path)

        for file in files:
            process_file = True
            for item in files_to_ignore:
                if file.strip() == item.strip():
                    process_file = False
                    break

            if process_file:
                self.logger.info("Copying file to watch directory - {file}".format(file=file))
                destination = file.replace("/home/{rUser}/data/{user}/torrents".format(rUser=rTorrentUsername,user=rUser),
                                "/home/{rUser}/data/{user}/watch".format(rUser=rTorrentUsername, user=rUser))
                remote_interface.copy_files(file, destination)

    def run(self):
        remote_interface = self.remoteIO

        while True:
            try:
                self.logger.info("Running the seedbox thread")
                self.logger.info("Connecting to the seedbox using ssh")

                self.logger.info("Connecting to the rTorrent interface")
                torrent_interface = ruTorrent(rTorrentURL, rTorrentUsername, rTorrentPassword, wwwUser)

                self.logger.info('Checking the connection and reconnecting if necessasary')
                remote_interface.check_connection()

                previous_processed_torrents = remote_interface.get_index_file(rUser)
                logger.info("Previous torrents detected as {processed_torrent}".format(
                    processed_torrent=previous_processed_torrents))
                new_copied_files = dict()

                for hash in torrent_interface.get_torrent_indicators():
                    if torrent_interface.torrent_user(hash) == rUser:
                        if torrent_interface.is_torrent_seeding(hash):
                            if hash in previous_processed_torrents.keys():
                                torrent_complete = time.strptime(previous_processed_torrents[hash], "%Y-%m-%d")
                                if ( datetime.datetime(*torrent_complete[:6]) + datetime.timedelta(days=rTorrentSeedingDays)) < \
                                    datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                                    self.logger.info("Cleaning up torrent - {torrent}".format(torrent=hash))
                                    for path in torrent_interface.get_file_lists(hash):
                                        remote_interface.delete_files(path)
                                    torrent_interface.remove_torrent(hash)
                                else:
                                    self.logger.info("No changes on torrent - {torrent}".format(torrent=hash))
                                    new_copied_files[hash] = previous_processed_torrents[hash]
                            else:
                                self.logger.info("Registering new torrent - {torrent}".format(torrent=hash))
                                self.copy_torrent(remote_interface, torrent_interface, hash)
                                new_copied_files[hash] = time.strftime("%Y-%m-%d")

                self.logger.info("Saving index file")
                remote_interface.write_index_file(new_copied_files, rUser)
            except Exception as ie:
                self.logger.exception(ie)

            self.logger.info("Done with the Seedbox thread, sleeping for 5 minutes")
            time.sleep(5*60)


class Downloader(threading.Thread):
    show_mapper = {"Scandal (US)":"Scandal (2012)"}

    def __init__(self, logger, remoteIO):
        threading.Thread.__init__(self)
        self.logger = logger
        self.remoteIO = remoteIO

    def guess_details(self, path):
        result = {}
        guess = guess_file_info(path, info='filename')

        if guess['type'] == "episode":
            name = guess['series']

            if name in self.show_mapper:
                name = self.show_mapper[name]

            result["type"] = "tv"
            result["show"] = name
            result["season"] = guess["season"]

            if guess.has_key("year"):
                result["year"] = guess["year"]

            if guess.has_key("episodeList"):
                result["double_episode"] = 1
                result["episode"] = guess["episodeList"][0]
            else:
                result["double_episode"] = 0
                result["episode"] = guess["episodeNumber"]

            t = tvdb_api.Tvdb()
            if t[name][result["season"]][result["episode"]]["episodename"] is None:
                return []
            else:
                result['name'] = t[name][result["season"]][result["episode"]]["episodename"]
                return result

            return result
        elif guess['type'] == "movie":
            result["type"] = "movie"
            result["name"] = guess["title"]
            result["year"] = guess["year"]

            return result

        return []

    def __get_destination__(self, details, extension):
        if details['type'] == 'tv':
            if details['double_episode'] == 0:
                output = "{show} - S{season}E{episode} - {showname}{ext}".format(
                    show = details["show"], season = str(details["season"]).zfill(2),
                    episode = str(details["episode"]).zfill(2), showname = str(details["name"]),
                    ext = extension)
            else:
                output = "{show} - S{season}E{episode}-E{episode1} - {showname}{ext}".format(
                    show = details["show"], season = str(details["season"]).zfill(2),
                    episode = str(details["episode"]).zfill(2), showname = str(details["name"]),
                    ext = extension, episode1 = str(int(details["episode"])+1).zfill(2))

            return os.path.join(ariaCompleteDir, "TV Shows", details["show"], 'Season ' +
                             str(details["season"]).zfill(2), output)
        elif details['type'] == 'movie':
            path = "{name} ({year}){ext}".format(name=details["name"], year=details["year"],ext=extension)

            return os.path.join(ariaCompleteDir, "Movies", path)

    def run(self):
        remote_interface = self.remoteIO

        while True:
            try:
                published_downloads = []
                base_dir = "/home/{rTorrentUsername}/data/{rUser}/watch".format(rTorrentUsername=rTorrentUsername, rUser=rUser)

                self.logger.info("Connecting to the local aria downloader")
                aria_interface = aria(ariaURL, ariaPort)

                self.logger.info("Connecting to the seedbox")
                self.logger.info('Checking the connection and reconnecting if necessasary')
                remote_interface.check_connection()

                avail_files = remote_interface.get_file_list(base_dir)

                for curr_file in sorted(avail_files.items(), key=operator.itemgetter(1)):
                    file = curr_file[0]
                    aria_id = aria_interface.register_download(
                    remote_interface.get_http_url(file, wwwUser), os.path.dirname(ariaIncompleteDir + file[len(base_dir):]))
                    published_downloads.append({"aria":aria_id, "remote_path": file})

                self.logger.info("Available downloads detected as - {download}".format(download=published_downloads))

                while len(published_downloads) > 0:
                    new_published_downloads = []
                    for download in published_downloads:
                        aria_id = download["aria"]
                        remote_file = download["remote_path"]

                        if aria_interface.is_download_in_progress(aria_id):
                            new_published_downloads.append({"aria":aria_id, "remote_path": remote_file})
                        elif aria_interface.is_download_done(aria_id):
                            try:
                                self.logger.info("Download done of {download}, processing file".format(download=remote_file))
                                file = aria_interface.get_destination_files(aria_id)
                                destination = ariaCompleteDir + file[len(ariaIncompleteDir):]

                                if isRenameEnabled:
                                    try:
                                        file_details = download.guess_details(
                                            file[len(ariaIncompleteDir):]), os.path.splitext(file)[1]

                                        if len(file_details) > 0:
                                            destination = download.__get_destination__(file_details)
                                    except:
                                        None

                                aria_interface.purge_download(aria_id)
                                remote_interface.delete_files(remote_file)

                                if os.path.exists(destination):
                                    os.remove(destination)

                                if not os.path.exists(os.path.dirname(destination)):
                                    os.makedirs(os.path.dirname(destination))

                                os.rename(file, destination)
                                self.logger.info("Done processing file, {file}".format(file=remote_file))
                            except Exception as ie:
                                self.logger.exception(ie)
                        elif aria_interface.is_download_error(aria_id):
                            self.logger.info("A error occured with download {download}, cleaning up".format(download=remote_file))
                            aria_interface.purge_download(aria_id)

                    published_downloads = new_published_downloads
                    time.sleep(10)
            except Exception as ie:
                self.logger.exception(ie)

            self.logger.info("Done with the Downloader thread, sleeping for 5 minutes")
            time.sleep(5*60)


class Transcoder(threading.Thread):
    def __init__(self, logger):
        threading.Thread.__init__(self)
        self.logger = logger

    def run(self):
        while True:
            try:
                s = xmlrpclib.ServerProxy(TranscodingServer, allow_none=True)

                for root, dirnames, filenames in os.walk(ariaCompleteDir):
                    for filename in fnmatch.filter(filenames, '*'):
                        file = os.path.join(root, filename).replace(ariaCompleteDir,'')
                        self.logger.info("Detected file to process - {file}".format(file=file))

                        try:
                            result = s.guess_details(file)
                            self.logger.info("File guessed as - {guess}".format(guess=result))

                            if len(result) > 0:
                                if result["type"] == "tv":
                                    year = None
                                    if "year" in result:
                                        year = result["year"]

                                    self.logger.info("Publishing tv show file to the transcoder queue")
                                    s.add_tv_show_queue(os.path.join(root, filename), result["show"], result["season"], result["episode"], result["double_episode"], year)
                                elif result["type"] == "movie":
                                    self.logger.info("Publishing movie to the transcoder queue")
                                    s.add_movie_queue(os.path.join(root, filename), result["name"], result["year"])
                        except Exception as ie:
                            self.logger.exception(ie)
            except Exception as ie:
                self.logger.exception(ie)

            self.logger.info("Done with the Transcoder thread, sleeping for 5 minutes")
            time.sleep(5*60)

if __name__== "__main__":
    #main interface
    rTorrentURL = "fr27463.pulsedmedia.com"
    rTorrentUsername = "jhanekom"
    rTorrentPassword = "9nJwx702Qj"
    rUser = "jaco"
    rTorrentSeedingDays=4
    TranscodingServer = 'http://localhost:8000/handbrake'

    wwwUser = "user-jhanekom"
    ariaURL = "192.168.0.2"
    ariaPort = 6800
    ariaIncompleteDir = "/home/jhanekom/Downloads/incomplete"
    ariaCompleteDir = "/home/jhanekom/Downloads/complete"
    isRenameEnabled = False

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create a file handler
    handler = logging.FileHandler(os.path.join(os.path.dirname(sys.argv[0]),"rutorrent-sync-aria.log"))
    handler.setLevel(logging.DEBUG)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    logger.info("Starting the application")

    logger.info("Connecting to the seedbox")
    remoteIO = remoteIO(rTorrentURL, rTorrentUsername, rTorrentPassword)

    logger.info("Starting the seedbox")
    Seedbox(logger, remoteIO).start()

    logger.info("Starting the downloader")
    Downloader(logger, remoteIO).start()

    logger.info("Starting the transcoder")
    Transcoder(logger).start()

    logger.info("All threads started up successfully")
