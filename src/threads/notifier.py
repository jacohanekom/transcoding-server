__author__ = 'jacohanekom'

import utils, time
from hachoir_core.cmd_line import unicodeFilename
from hachoir_metadata import extractMetadata
from hachoir_parser import createParser
import sqlite3 as lite

class NotifierThread(utils.Base):
    def __mark_episode_as_done__(self, show_name, season, episode, status):
        con = None

        try:
            con = lite.connect(super(NotifierThread, self).get_config()['NOTIFIER_SICKBEARD_DATABASE_PATH'])

            cur = con.cursor()
            cur.execute("SELECT indexer_id FROM tv_shows WHERE show_name = '{show_name}'".format(show_name=show_name))

            data = cur.fetchone()

            if len(data) > 0:
                cur.execute("UPDATE tv_episodes SET status = ? WHERE showid=? AND season=? AND episode=?",
                            (status, data[0], season, episode))


        except lite.Error, e:
            print "Unable to register show"
        finally:
            if con:
                con.commit()
                con.close()

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

                if hasattr(file, "destination"):
                    if file.metadata.type == 'tv':
                        self.__mark_episode_as_done__(file.metadata.show,
                                                      file.metadata.season,
                                                      file.metadata.episode,
                                                      self.__get_sickbeard_indicator__(file))
                    elif file.metadata.type == 'movie':
                        None

            time.sleep(60)