__author__ = 'jacohanekom'

import utils, time, os, urllib2, urllib, json
import sqlite3 as lite
import xml.dom.minidom as minidom

class NotifierThread(utils.Base):
    def __mark_episode_as_done__(self, show_name, season, episode, status, destination):
        con = None

        try:
            con = lite.connect(super(NotifierThread, self).get_config()['NOTIFIER_SICKBEARD_DATABASE_PATH'])

            cur = con.cursor()
            cur.execute("SELECT indexer_id FROM tv_shows WHERE show_name = '{show_name}'".format(show_name=show_name))

            data = cur.fetchone()

            if len(data) > 0:
                cur.execute("UPDATE tv_episodes SET status=?, location=?, file_size=? WHERE showid=? AND season=? AND episode=?",
                            (status, os.path.join(destination[0], destination[1]), os.path.getsize(os.path.join(destination[0],
                                destination[1])), data[0], season, episode))

        except lite.Error, e:
            print "Unable to register show"
        finally:
            if con:
                con.commit()
                con.close()

    def __mark_movie_as_done__(self, url, key, movie):
        data = json.load(urllib2.urlopen("{url}/api/{key}/media.list".format(url=url, key=key)))
        id_list = []

        for curr_movie in data['movies']:
            try:
                for title in curr_movie['info']['titles']:
                    if title == movie:
                        id_list.append(curr_movie['_id'])
                        break
            except:
                None

        for id in id_list:
            urllib2.urlopen("{url}/api/{key}/media.delete?id={id}".format(url=url, key=key, id=id))

        data = json.load(urllib2.urlopen("{url}/api/{key}/manage.update?full=1".format(url=url, key=key)))


    def __update_plex__(self, plex_host, plex_port):
        source_type = ['movie', 'show']
        base_url = 'http://%s:%s/library/sections' % (plex_host,plex_port)
        refresh_url = '%s/%%s/refresh' % base_url

        try:
           xml_sections = minidom.parse(urllib.urlopen(base_url))
           sections = xml_sections.getElementsByTagName('Directory')
           for s in sections:
               if s.getAttribute('type') in source_type:
                  url = refresh_url % s.getAttribute('key')
                  urllib.urlopen(url)
        except:
           None


    def __get_sickbeard_indicator__(self, file):
        result = 3276804

        if hasattr(file, "hd_indicator"):
            indicator = file.hd_indicator
            if indicator == 0:
                result = 104
            elif indicator == 1:
                result = 404
            elif indicator == 2:
                result = 1604

        return result

    def run(self):
        print 'Starting ' + super(NotifierThread, self).get_name()

        while True:
            for uuid in super(NotifierThread, self).get_available_files():
                file = super(NotifierThread, self).get_storage(uuid)
                file.status.state = super(NotifierThread, self).state_text(1)

                if hasattr(file, "destination"):
                    if file.metadata.type == 'tv':
                        self.__mark_episode_as_done__(file.metadata.show,
                                                      file.metadata.season,
                                                      file.metadata.episode,
                                                      self.__get_sickbeard_indicator__(file),
                                                      file.destination)
                    elif file.metadata.type == 'movie':
                        self.__mark_movie_as_done__(
                            super(NotifierThread, self).get_config()['NOTIFIER_COUCHPOTATO_URL'],
                            super(NotifierThread, self).get_config()['NOTIFIER_COUCHPOTATO_KEY'],
                            file.metadata.name)

                self.__update_plex__(super(NotifierThread, self).get_config()['NOTIFIER_PLEX_HOST'],
	                             super(NotifierThread, self).get_config()['NOTIFIER_PLEX_PORT'])
                file.status.state = super(NotifierThread, self).state_text(2)
                super(NotifierThread, self).update_storage(uuid, file)
            time.sleep(60)