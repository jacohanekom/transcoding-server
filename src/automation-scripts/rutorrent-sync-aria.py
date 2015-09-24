__author__ = 'Jaco-Hanekom'

import xmlrpclib, paramiko, os, tempfile, uuid, json, time, datetime, sys, fnmatch, socket, traceback

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

    def copy_files(self, source, destination):
        self.ssh.exec_command('mkdir -p "{directory}"'.format(directory=os.path.dirname(destination)))
        self.ssh.exec_command('cp "{source}" "{destination}"'.format(source=source, destination=destination))

    def get_file_list(self, path, file_list=None):
        if file_list is None:
            file_list = []

        for dir in self.sftp.listdir(path=path):
            if int(oct(self.sftp.stat(os.path.join(path, dir)).st_mode)[0:2]) == 4:
                file_list += self.get_file_list(os.path.join(path, dir),  file_list=file_list)
            else:
                file_list.append(os.path.join(path, dir))

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

def copy_torrent(torrent):
    files = torrentInterface.get_file_lists(torrent)
    files_to_ignore = []

    for file in files:
        if file.endswith("rar"):
            path = os.path.dirname(file).replace("/home/{rUser}/data/{user}/torrents".format(rUser=rTorrentUsername,user=rUser),
                                          "/home/{rUser}/data/{user}/watch".format(rUser=rTorrentUsername, user=rUser))
            files_to_ignore = remoteInterface.remote_unrar(file, path)

    for file in files:
        process_file = True
        for item in files_to_ignore:
            if file.strip() == item.strip():
                process_file = False
                break

        if process_file:
            destination = file.replace("/home/{rUser}/data/{user}/torrents".format(rUser=rTorrentUsername,user=rUser),
                                "/home/{rUser}/data/{user}/watch".format(rUser=rTorrentUsername, user=rUser))
            remoteInterface.copy_files(file, destination)

if len(sys.argv) == 1:
    print "Please specify atleast one argument"
else:
    global lock_socket   # Without this our lock gets garbage collected

    try:
        #lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        #lock_socket.bind('\0' + sys.argv[1])

        remoteInterface = remoteIO(rTorrentURL, rTorrentUsername, rTorrentPassword)

        if sys.argv[1] == 'rtorrent':
            torrentInterface = ruTorrent(rTorrentURL, rTorrentUsername, rTorrentPassword, wwwUser)

            previous_processed_torrents = remoteInterface.get_index_file(rUser)
            new_copied_files = dict()

            for hash in torrentInterface.get_torrent_indicators():
                if torrentInterface.torrent_user(hash) == rUser:
                    if torrentInterface.is_torrent_seeding(hash):
                        if hash in previous_processed_torrents.keys():
                            torrent_complete = time.strptime(previous_processed_torrents[hash], "%Y-%m-%d")
                            if ( datetime.datetime(*torrent_complete[:6]) + datetime.timedelta(days=rTorrentSeedingDays)) < \
                                datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                                for path in torrentInterface.get_file_lists(hash):
                                    remoteInterface.delete_files(path)
                                torrentInterface.remove_torrent(hash)
                            else:
                                new_copied_files[hash] = previous_processed_torrents[hash]
                        else:
                            copy_torrent(hash)
                            new_copied_files[hash] = time.strftime("%Y-%m-%d")

            remoteInterface.write_index_file(new_copied_files, rUser)
        elif sys.argv[1] == 'aria':
            ariaInterface = aria(ariaURL, ariaPort)
            published_downloads = []
            base_dir = "/home/{rTorrentUsername}/data/{rUser}/watch".format(rTorrentUsername=rTorrentUsername, rUser=rUser)

            for file in remoteInterface.get_file_list(base_dir):
                aria_id = ariaInterface.register_download(
                    remoteInterface.get_http_url(file, wwwUser), os.path.dirname(ariaIncompleteDir + file[len(base_dir):]))
                published_downloads.append({"aria":aria_id, "remote_path": file})

            while len(published_downloads) > 0:
                new_published_downloads = []
                for download in published_downloads:
                    aria_id = download["aria"]
                    remote_file = download["remote_path"]

                if ariaInterface.is_download_in_progress(aria_id):
                    new_published_downloads.append({"aria":aria_id, "remote_path": file})
                elif ariaInterface.is_download_done(aria_id):
                    file = ariaInterface.get_destination_files(aria_id)
                    destination = ariaCompleteDir + file[len(ariaIncompleteDir):]

                    ariaInterface.purge_download(aria_id)
                    remoteInterface.delete_files(remote_file)

                    if os.path.exists(destination):
                        os.remove(destination)

                    os.makedirs(os.path.dirname(destination))
                    os.rename(file, destination)
                elif ariaInterface.is_download_error(aria_id):
                    ariaInterface.purge_download(aria_id)

            published_downloads = new_published_downloads
            time.sleep(10)
        elif sys.argv[1] == "local_watch":
            s = xmlrpclib.ServerProxy(TranscodingServer, allow_none=True)
            for root, dirnames, filenames in os.walk(ariaCompleteDir):
                for filename in fnmatch.filter(filenames, '*'):
                    file = os.path.join(root, filename).replace(ariaCompleteDir,'')

                try:
                    result = s.guess_details(file)

                    if len(result) > 0:
                        if result["type"] == "tv":
                            year = None
                            if "year" in result:
                                year = result["year"]

                            s.add_tv_show_queue(os.path.join(root, filename), result["show"], result["season"], result["episode"], result["double_episode"], year)
                        elif result["type"] == "movie":
                            s.add_movie_queue(os.path.join(root, filename), result["name"], result["year"])
                except:
                    print "Do not publish {file}".format(file=file)
    except:
        print(traceback.format_exc())