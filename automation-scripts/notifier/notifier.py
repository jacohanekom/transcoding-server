__author__ = 'Jaco-Hanekom'
import sqlite3 as lite
import sys, os, urllib2
from hachoir_core.cmd_line import unicodeFilename
from hachoir_metadata import extractMetadata
from hachoir_parser import createParser
import urllib
from xml.dom import minidom
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

class CouchPotato():
    def __init__(self, url, api_key):
        self.api_key = api_key
        self.url = url

    def trigger_refresh(self):
        try:
            request = urllib2.urlopen('{base}/api/{api}/manage.update?full=true'.format(base = self.url, api=self.api_key))
            request.close()
        finally:
            None

class Plex():
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def refresh(self):
        source_type = ['movie', 'show'] # Valid values: artist (for music), movie, show (for tv)
        base_url = 'http://{host}:{port}/library/sections'.format(host=self.host, port=self.port)
        refresh_url = '%s/%%s/refresh?force=1' % base_url

        try:
            xml_sections = minidom.parse(urllib.urlopen(base_url))
            sections = xml_sections.getElementsByTagName('Directory')
            for s in sections:
                if s.getAttribute('type') in source_type:
                    url = refresh_url % s.getAttribute('key')
                    x = urllib.urlopen(url)
        except:
            pass

class SickRage():
    def __init__(self, url, db_location):
        self.url = url
        self.db_location = db_location

    def process_file(self, file):
        try:
            paths = file.split("/")
            path = ""

            for i in range(len(paths)-2):
                path += paths[i] + "/"

            path_id = self.__get_show_identifier__(path[:-1])
            episode_id = self.__get_episode_number__(file)

            if path_id and episode_id:
                response = urllib2.urlopen('{base}/home/setStatus?show={show}&status={status}&eps={eps}'.format(base=self.url,
                    show=path_id, status=self.__get_hd_tag__(file), eps=episode_id))
                response.close()
        except:
            None

    def __get_hd_tag__(self, video):
        result = 104

        file_metadata = extractMetadata(createParser(unicodeFilename(video)))
        if file_metadata.get('width') == 1280:
            result = 404
        elif file_metadata.get('width') == 1920:
            result = 1604

        return result

    def __get_show_identifier__(self, show_path):
        con = None
        id = None

        try:
            con = lite.connect(self.db_location)
            cur = con.cursor()
            cur.execute("SELECT indexer_id FROM tv_shows WHERE location = '{directory}'".format(directory=show_path))
            id = cur.fetchone()[0]
        finally:
            if con:
                con.close()

            return id

    def __get_episode_number__(self, file):
        filename = os.path.split(file)[1].split(" - ")
        episode = None

        if len(filename) == 3:
            ep_details = filename[1]

            if "-" in ep_details:
                episode = str(int(ep_details[1:3])) + "x" + str(int(ep_details[4:6])) + "|" + \
                          str(int(ep_details[1:3])) + "x" + str(int(ep_details[8:10]))
            else:
                episode = str(int(ep_details[1:3])) + "x" + str(int(ep_details[4:6]))

        return episode


class MediaHandler(PatternMatchingEventHandler):
    patterns = ["*.m4v"]

    rage = SickRage("http://127.0.0.1/sickrage", "/home/jhanekom/Applications/SickRage/sickbeard.db")
    couchPotato = CouchPotato("http://127.0.0.1/couchpotato", "716e4e6d9d764d8cafb6bf46cf4f2dd2")
    plex = Plex('127.0.0.1',32400)

    def process(self, event):
        print event.src_path  # print now only for debug

        if 'TV Shows' in event.src_path:
            self.rage.process_file()
        elif 'Movies' in event.src_path:
            self.couchPotato.trigger_refresh()

        self.plex.refresh()

    def on_modified(self, event):
        self.process(event)


if __name__ == '__main__':
    paths = ["/media/media_a_g/TV Shows", "/media/media_a_g/Movies", "/media/media_h_q/TV Shows", "/media/media_h_q/Movies",
             "/media/media_r_s/TV Shows", "/media/media_r_s/Movies", "/media/media_t_z/TV Shows", "/media/media_t_z/Movies"]
    observer = Observer()

    for path in paths:
        observer.schedule(MediaHandler(), path=path)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
