import time
import os
import tempfile
import pytumblr
import tvdb_api, tvdb_exceptions
import urllib
import subprocess
import tmdbsimple as tmdb
import xmlformatter
import traceback
from hachoir_core.cmd_line import unicodeFilename
from hachoir_metadata import extractMetadata
from hachoir_parser import createParser
import utils, sys

class MetadataThread(utils.Base):
    def __clean_string__(self, val):
        try:
            cleaned = ''.join([i if ord(i) < 128 else ' ' for i in val])
            cleaned = cleaned.encode('ascii', 'xmlcharrefreplace')

            return cleaned.replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
        except:
            print sys.exc_info()[0]
            return ""

    def get_movie_metadata(self, movie, year):
        try:
            tags = {}
            results = {}
            search = tmdb.Search()
            search.movie(query=movie)
            for s in search.results:
                if 'release_date' in s:
                    if int(s['release_date'][0:4]) == int(year):
                        response = tmdb.Movies(s['id'])
                        break

            if response:
                results['--title'] = self.__clean_string__(response.info()['title'])
                results['--comment'] = self.__clean_string__('Information courtesy of The Movie Database (http://www.themoviedb.com). Used with permission.')
                results['--genre'] = self.__clean_string__(response.info()['genres'][0]['name'])
                results['--year'] = self.__clean_string__('{time}T10:00:00Z'.format(time=response.info()['release_date']))

                results['--description'] = self.__clean_string__(response.info()['tagline'][:255] + (response.info()['tagline'][255:] and '..'))
                results['--longdesc'] = self.__clean_string__(response.info()['overview'])

                results['--stik'] = 'Short Film'
                results['--advisory'] = 'Inoffensive'
                results['--gapless'] = 'false'

                actors = []
                directors = []
                producers = []
                screenwriters = []
                production_companies = ''
                for credit in response.credits()['cast']:
                    actors.append(self.__clean_string__(credit['name']))

                for crew in response.credits()['crew']:
                    if crew['department'] == 'Directing':
                        directors.append(self.__clean_string__(crew['name']))
                    elif crew['department'] == 'Writing':
                        screenwriters.append(self.__clean_string__(crew['name']))
                    elif crew['department'] == 'Production':
                        producers.append(self.__clean_string__(crew['name']))

                for company in response.info()['production_companies']:
                    production_companies += ', ' + self.__clean_string__(company['name'])

                results['--artist'] = directors[0]
                tags['com.apple.iTunes;iTunEXTC'] = 'us-tv|{contentrating}|200|'.format(contentrating=self.__clean_string__(response.releases()['countries'][0]['certification']))
                all_data = []
                all_data.append(self.__get_dictionary_plist__('cast', actors))
                all_data.append(self.__get_dictionary_plist__('directors', directors))
                all_data.append(self.__get_dictionary_plist__('producers', producers))
                all_data.append(self.__get_dictionary_plist__('screenwriters', screenwriters))
                tags['com.apple.iTunes;iTunMOVI'] = self.__build_plist__(all_data, production_companies[2:])
                tags['standard'] = results
                tags['imdb_id'] = response.info()['imdb_id']
                return tags
            else:
                return None
        except:
            return None

    def get_tv_metadata(self, show_name, season, episode, year=None):
        tags = {}
        results = {}
        tvdb_interface = tvdb_api.Tvdb(actors=True)

        try:
            if year:
                try:
                    show = tvdb_interface[show_name + ' (' + str(year) + ')']
                except tvdb_exceptions.tvdb_shownotfound:
                    show = tvdb_interface[show_name]
            else:
                show = tvdb_interface[show_name]

            if show:
                results['--title'] = self.__clean_string__(show[season][episode]['episodename'])
                results['--artist'] = self.__clean_string__(show['seriesname'])
                results['--album'] = self.__clean_string__('{showName}, season {season}'.format(showName=show['seriesname'], season=season))
                results['--comment'] = self.__clean_string__('Information courtesy of The TVDB (http://www.thetvdb.com). Used with permission.')
                results['--genre'] = self.__clean_string__(show['genre'][1:].split('|')[0])
                results['--year'] = self.__clean_string__('{time}T10:00:00Z'.format(time=show[season][episode]['firstaired']))
                results['--tracknum'] = self.__clean_string__('{ep}/{total}'.format(ep=episode, total=len(show[season])))
                results['--disk'] = self.__clean_string__('{season}/{total}'.format(season=season, total=len(show)))
                results['--TVShowName'] = self.__clean_string__(show['seriesname'])
                results['--TVNetwork'] = self.__clean_string__(show['network'])
                results['--TVEpisode'] = self.__clean_string__('S{season}E{episode}'.format(season=str(season).zfill(2), episode=str(episode).zfill(2)))
                results['--TVSeasonNum'] = season
                results['--TVEpisodeNum'] = episode

                results['--description'] = self.__clean_string__(show[season][episode]['overview'][:255] + (show[season][episode]['overview'][255:] and '..'))
                results['--longdesc'] = self.__clean_string__(show[season][episode]['overview'])

                results['--storedesc'] = self.__clean_string__(show['overview'])
                results['--stik'] = 'TV Show'
                results['--advisory'] = 'Inoffensive'
                results['--gapless'] = 'false'

                if 'poster' in show.data.keys():
                    destination = os.path.join(tempfile.gettempdir(), show['poster'].split('/')[(len(show['poster'].split('/')) - 1)])
                    urllib.urlretrieve(show['poster'], destination)
                    results['--artwork'] = destination

                plist_records = []
                plist_records.append(self.__get_dictionary_plist__('cast', self.__get_split_list__(show['actors'])))
                plist_records.append(self.__get_dictionary_plist__('directors', self.__get_split_list__(show[season][episode]['director'])))
                plist_records.append(self.__get_dictionary_plist__('screenwriters', self.__get_split_list__(show[season][episode]['writer'])))
                tags['standard'] = results
                tags['com.apple.iTunes;iTunMOVI'] = self.__build_plist__(plist_records)
                contentrating = 'TV-14'

                if show['contentrating'] is not None:
                    contentrating = show['contentrating']

                tags['com.apple.iTunes;iTunEXTC'] = 'us-tv|{contentrating}|500|'.format(contentrating=contentrating)
                tags['id'] = show[season][episode]["seasonid"]
                return tags
            else:
                raise "Unable to find show - {show}".format(show=show_name)
        except:
            raise self.exc_info[1], None, self.exc_info[2]

    def __build_plist__(self, values, studio = None):
        formatter = xmlformatter.Formatter(indent='1', indent_char='\t', encoding_output='ISO-8859-1', preserve=['literal'])
        output = '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        output += '<plist version="1.0">'
        output += '<dict>'
        for rec in values:
            output += rec

        if studio:
            output += '<key>studio</key>'
            output += '<string>{studio}</string>'.format(studio=studio)

        output += '</dict>'
        output += '</plist>'

        print output

        return formatter.format_string(output)

    def __get_split_list__(self, value):
        result = []

        if value is not None:
            if value.startswith('|'):
                for val in value[1:-1].split('|'):
                    result.append(self.__clean_string__(val))
            else:
                result.append(self.__clean_string__(value))

            return result
        else:
            return result

    def __get_dictionary_plist__(self, name, list):
        output = '<key>{name}</key>'.format(name=name.encode('utf-8'))
        output += '<array>'
        for value in list:
            output += '<dict>'
            output += '<key>{name}</key>'.format(name='name')
            output += '<string>{name}</string>'.format(name=value)
            output += '</dict>'
        output += '</array>'
        return output

    def get_tumbler_cover_art(self, season_id):
        t = tvdb_api.Tvdb(banners=True)

        client = pytumblr.TumblrRestClient(super(MetadataThread, self).get_config()['METADATA_TUMBLR_KEY'])
        results = client.posts('squaredtvart.tumblr.com', tag='thetvdb season {seasonid}'.format(seasonid=season_id))
        if results['total_posts'] > 0:
            source = results['posts'][0]['photos'][0]['original_size']['url']
            destination = os.path.join(tempfile.gettempdir(), source.split('/')[(len(source.split('/')) - 1)])
            urllib.urlretrieve(source, destination)

            return destination

    def get_movie_cover_art(self, movie, year):
        search = tmdb.Search()

        search.movie(query=movie)
        for s in search.results:
            if int(s['release_date'][0:4]) == int(year):
                if s['poster_path'] is not None:
                    source = 'http://image.tmdb.org/t/p/w500' + s['poster_path']
                    destination = os.path.join(tempfile.gettempdir(), source.split('/')[(len(source.split('/')) - 1)])
                    urllib.urlretrieve(source, destination)

                    return destination

    def tag_atomic_parsley(self, uuid, file, tags):
        output = os.path.join(tempfile.gettempdir(), uuid + super(MetadataThread, self).get_config()['HANDBRAKE_EXTENSION'])

        cmd_to_execute = []
        iTunMOVI = tags['com.apple.iTunes;iTunMOVI']
        iTunEXTC = tags['com.apple.iTunes;iTunEXTC']
        for (key, value,) in tags['standard'].iteritems():
            cmd_to_execute.append(str(key))
            cmd_to_execute.append(str(value))

        atomic_parsley_path = super(MetadataThread, self).get_config()['METADATA_ATOMIC_PARSLEY']

        cmd = [atomic_parsley_path, output] + cmd_to_execute + ['--rDNSatom',
         iTunMOVI,
         'name=iTunMOVI',
         'domain=com.apple.iTunes'] + ['--rDNSatom',
         iTunEXTC,
         'name=iTunEXTC',
         'domain=com.apple.iTunes']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

        while True:
            out = proc.stdout.readline()
            content = repr(out)

            if 'Finished writing to temp file' in content:
                file.status.metadata = 100
                super(MetadataThread, self).update_storage(uuid, file)
                self.__move_tagged_file(uuid)
                return True
            elif 'Progress' in content:
                if not hasattr(file.status, "metadata"):
                    setattr(file.status, "metadata", 0)

                file.status.metadata = int(content[content.index('%')-3:][:3].replace(' ',''))
                super(MetadataThread, self).update_storage(uuid, file)


    def __move_tagged_file(self, uuid):
        output = os.path.join(tempfile.gettempdir(), uuid + super(MetadataThread, self).get_config()['HANDBRAKE_EXTENSION'])
        os.remove(output)

        for file in os.listdir(tempfile.gettempdir()):
            if str(file).startswith(uuid):
                os.rename(os.path.join(tempfile.gettempdir(), str(file)), output)
                return


    def get_hd_tag(self, video):
        result = 0

        try:
            file_metadata = extractMetadata(createParser(unicodeFilename(video)))
            if file_metadata.get('width') == 1280:
                result = 1
            elif file_metadata.get('width') == 1920:
                result = 2
        finally:
            return result


    def __init__(self, registered_files, config):
        super(MetadataThread, self).__init__(registered_files, config)
        tmdb.API_KEY = super(MetadataThread, self).get_config()['METADATA_MOVIE_KEY']

    def process_file(self, uuid, file):
        output = os.path.join(tempfile.gettempdir(), uuid + super(MetadataThread, self).get_config()['HANDBRAKE_EXTENSION'])

        if file.metadata.type == 'tv':
            tags = self.get_tv_metadata(
                file.metadata.show,file.metadata.season,
                file.metadata.episode, getattr(file.metadata, "year", None))

            if tags:
                cover_image = self.get_tumbler_cover_art(tags["id"])
                if cover_image :
                    tags['standard']['--artwork'] = cover_image

                if '--artist' in tags['standard']:
                    file.metadata.show = tags['standard']['--artist'].replace(":", " ").replace("/", " ")

                if '--title' in tags['standard']:
                    setattr(file.metadata, "title", tags['standard']['--title'].replace(":", " ").replace("/", " "))
        elif file.metadata.type == 'movie':
            tags = self.get_movie_metadata(file.metadata.name, file.metadata.year)

            if tags:
                cover_image = self.get_movie_cover_art(file.metadata.name, file.metadata.year)

                if cover_image:
                    tags['standard']['--artwork'] = cover_image

        if tags:
            tags['standard']['--hdvideo'] = self.get_hd_tag(output)
            setattr(file, "hd_indicator", tags['standard']['--hdvideo'])

            if 'imdb_id' in tags:
                setattr(file, "imdb_id", tags['imdb_id'])

            self.tag_atomic_parsley(uuid, file, tags)

        file.status.state = super(MetadataThread, self).state_text(2)
        return file

    def run(self):

        print 'Starting ' + super(MetadataThread, self).get_name()
        while True:
            for uuid in super(MetadataThread, self).get_available_files():
                file = super(MetadataThread, self).get_storage(uuid)
                try:
                    file.status.state = super(MetadataThread, self).state_text(1)
                    super(MetadataThread, self).update_storage(uuid, file)

                    super(MetadataThread, self).update_storage(uuid, self.process_file(uuid, file))
                except:
                    file.status.state = super(MetadataThread, self).state_text(3,traceback.format_exc())
                    super(MetadataThread, self).update_storage(uuid, file)

            time.sleep(60)