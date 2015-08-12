import threading
import time
import math
import os
import tempfile
import config
import pytumblr
import tvdb_api
import urllib
import subprocess
import tmdbsimple as tmdb
import xmlformatter
import traceback
from hachoir_core.cmd_line import unicodeFilename
from hachoir_metadata import extractMetadata
from hachoir_parser import createParser

class metadataThread(threading.Thread):
    def updateStorage(self, uuid, obj):
        self.registered_files[uuid] = obj

    def getStorage(self, uuid):
        return self.registered_files[uuid]

    def getAvailableFiles(self):
        to_be_processed = list()
        for uuid in self.registered_files:
            if self.registered_files[uuid].status.state == 'metadata':
                to_be_processed.append(uuid)

        return to_be_processed

    def getMoviesMetaData(self, movie, year, hddvd, image):
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
            results['--title'] = response.info()['title']
            results['--artist'] = ''
            results['--comment'] = 'Information courtesy of The Movie Database (http://www.themoviedb.com). Used with permission.'
            results['--genre'] = response.info()['genres'][0]['name']
            results['--year'] = '{time}T10:00:00Z'.format(time=response.info()['release_date'])
            results['--description'] = response.info()['tagline'][:255] + (response.info()['tagline'][255:] and '..')
            results['--longdesc'] = response.info()['overview']
            results['--hdvideo'] = hddvd
            results['--stik'] = 'Short Film'
            results['--advisory'] = 'Inoffensive'
            results['--gapless'] = 'false'
            if image:
                results['--artwork'] = image
            actors = []
            directors = []
            producers = []
            screenwriters = []
            production_companies = ''
            for credit in response.credits()['cast']:
                actors.append(credit['name'])

            for crew in response.credits()['crew']:
                if crew['department'] == 'Directing':
                    directors.append(crew['name'])
                elif crew['department'] == 'Writing':
                    screenwriters.append(crew['name'])
                elif crew['department'] == 'Production':
                    producers.append(crew['name'])

            for company in response.info()['production_companies']:
                production_companies += ', ' + company['name']

            results['--artist'] = directors[0]
            tags['com.apple.iTunes;iTunEXTC'] = 'us-tv|{contentrating}|200|'.format(contentrating=response.releases()['countries'][0]['certification'])
            all_data = []
            all_data.append(self.getDictionaryPlist('cast', actors))
            all_data.append(self.getDictionaryPlist('directors', directors))
            all_data.append(self.getDictionaryPlist('producers', producers))
            all_data.append(self.getDictionaryPlist('screenwriters', screenwriters))
            tags['com.apple.iTunes;iTunMOVI'] = self.buildpList(all_data, production_companies[2:])
            tags['standard'] = results
            return tags
        else:
            return None

    def getTVShowMetaData(self, showName, season, episode, hddvd, image):
        tags = {}
        results = {}
        t = tvdb_api.Tvdb(actors=True)
        results['--title'] = t[showName][season][episode]['episodename']
        results['--artist'] = showName
        results['--album'] = '{showName}, season {season}'.format(showName=showName, season=season)
        results['--comment'] = 'Information courtesy of The TVDB (http://www.thetvdb.com). Used with permission.'
        results['--genre'] = t[showName]['genre'][1:].split('|')[0]
        results['--year'] = '{time}T10:00:00Z'.format(time=t[showName][season][episode]['firstaired'])
        results['--tracknum'] = '{ep}/{total}'.format(ep=episode, total=len(t[showName][season]))
        results['--disk'] = '{season}/{total}'.format(season=season, total=len(t[showName]))
        results['--TVShowName'] = showName
        results['--TVNetwork'] = t[showName]['network']
        results['--TVEpisode'] = 'S{season}E{episode}'.format(season=str(season).zfill(2), episode=str(episode).zfill(2))
        results['--TVSeasonNum'] = season
        results['--TVEpisodeNum'] = episode
        results['--description'] = t[showName][season][episode]['overview'][:255] + (t[showName][season][episode]['overview'][255:] and '..')
        results['--longdesc'] = t[showName][season][episode]['overview']
        results['--storedesc'] = t[showName]['overview']
        results['--hdvideo'] = hddvd
        results['--stik'] = 'TV Show'
        results['--advisory'] = 'Inoffensive'
        results['--gapless'] = 'false'

        if image:
            results['--artwork'] = image
        plist_records = []
        plist_records.append(self.getDictionaryPlist('cast', self.getSplitList(t[showName]['actors'])))
        plist_records.append(self.getDictionaryPlist('directors', self.getSplitList(t[showName][season][episode]['director'])))
        plist_records.append(self.getDictionaryPlist('screenwriters', self.getSplitList(t[showName][season][episode]['writer'])))
        tags['standard'] = results
        tags['com.apple.iTunes;iTunMOVI'] = self.buildpList(plist_records)
        contentrating = 'TV-14'
        if t[showName]['contentrating'] is not None:
            contentrating = t[showName]['contentrating']
        tags['com.apple.iTunes;iTunEXTC'] = 'us-tv|{contentrating}|500|'.format(contentrating=contentrating)
        return tags

    def buildpList(self, values, studio = None):
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
        return formatter.format_string(output)

    def getSplitList(self, value):
        result = []
        if value.startswith('|'):
            result = value[1:-1].split('|')
        else:
            result.append(value)
        return result

    def getDictionaryPlist(self, name, list):
        try:
           output = '<key>{name}</key>'.format(name=name.encode('utf-8'))
           output += '<array>'
           for value in list:
            	output += '<dict>'
            	output += '<key>{name}</key>'.format(name='name')
            	output += '<string>{name}</string>'.format(name=value.encode('utf-8'))
           output += '</dict>'
       	   output += '</array>'
           return output
	except:
	   return ""

    def getTVCoverArt(self, showName, season, episode):
        t = tvdb_api.Tvdb(banners=True)
        source = None
        destination = None
        try:
            client = pytumblr.TumblrRestClient(config.METADATA_TUMBLR_KEY)
            results = client.posts('squaredtvart.tumblr.com', tag='thetvdb season {seasonid}'.format(seasonid=t[showName][season][episode]['seasonid']))
            if results['total_posts'] > 0:
                source = results['posts'][0]['photos'][0]['original_size']['url']
            else:
                print 'No images found on sqaredtvart, going to thetvdb'
        except:
            print 'No images found on sqaredtvart, going to thetvdb'
        if source is None:
            try:
                rating = 0.0
                baseURL = 'http://thetvdb.com/banners/{image}'
                for (key, image,) in t[showName]['_banners']['season']['season'].iteritems():
                    if int(image['season']) == season:
                        if image['rating'] > rating:
                            url = baseURL.format(image=image['bannerpath'])
                            rating = image['rating']

            except:
                print 'No images found on thetvdb'
        if source is not None:
            try:
                destination = os.path.join(tempfile.gettempdir(), source.split('/')[(len(source.split('/')) - 1)])
                urllib.urlretrieve(source, destination)
            except:
                print 'No images found on all sources'
        else:
            print 'No images found on all sources'
        return destination

    def tagFile(self, file, tags):
        cmd_to_execute = []
        iTunMOVI = tags['com.apple.iTunes;iTunMOVI']
        iTunEXTC = tags['com.apple.iTunes;iTunEXTC']
        for (key, value,) in tags['standard'].iteritems():
            cmd_to_execute.append(str(key))
            cmd_to_execute.append(str(value))

        cmd = [config.METADATA_ATOMIC_PARSLEY, file] + cmd_to_execute + ['--rDNSatom',
         iTunMOVI,
         'name=iTunMOVI',
         'domain=com.apple.iTunes'] + ['--rDNSatom',
         iTunEXTC,
         'name=iTunEXTC',
         'domain=com.apple.iTunes'] + ['--overWrite']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        while proc.poll():
            None

        if proc.returncode == 0:
            print True
        else:
            return False

    def getMovieCoverArt(self, movieName, year):
        search = tmdb.Search()
        source = None
        destination = None
        try:
            search.movie(query=movieName)
            for s in search.results:
                if int(s['release_date'][0:4]) == int(year):
                    if s['poster_path'] is not None:
                        source = 'http://image.tmdb.org/t/p/w500' + s['poster_path']
                        break

        except:
            print 'Unable to get images for movie {movie}'.format(movie=movieName)
        if source is not None:
            try:
                destination = os.path.join(tempfile.gettempdir(), source.split('/')[(len(source.split('/')) - 1)])
                urllib.urlretrieve(source, destination)
            except:
                print 'No images found on all sources'
        else:
            print 'No images found on all sources'
        return destination

    def get_hd_tag(self, mediaFile):
        result = 0
        try:
            file_metadata = extractMetadata(createParser(unicodeFilename(mediaFile)))
            if file_metadata.get('width') == 1280:
                result = 1
            elif file_metadata.get('width') == 1920:
                result = 2
        except:
            None
        return result

    def __init__(self, registered_files):
        threading.Thread.__init__(self)
        self.registered_files = registered_files
        tmdb.API_KEY = config.METADATA_MOVIE_KEY

    def run(self):
        print 'Starting ' + self.name
        while True:
            for uuid in self.getAvailableFiles():
                file = self.getStorage(uuid)
                try:
                    print 'processing file - {file}'.format(file=file.file)
                    file.status.state = 'processing - metadata'
                    self.updateStorage(uuid, file)
                    output = os.path.join(tempfile.gettempdir(), uuid + config.HANDBRAKE_EXTENSION)
                    if file.metadata.type == 'tv':
                        tags = self.getTVShowMetaData(file.metadata.show, file.metadata.season, file.metadata.episode, self.get_hd_tag(output), self.getTVCoverArt(file.metadata.show, file.metadata.season, file.metadata.episode))
                    elif file.metadata.type == 'movie':
                        tags = self.getMoviesMetaData(file.metadata.name, file.metadata.year, self.get_hd_tag(output), self.getMovieCoverArt(file.metadata.name, file.metadata.year))
                    if tags:
                        self.tagFile(output, tags)
                    print 'done processing file - {file}'.format(file=file.file)
                    file.status.state = 'publish'
                    self.updateStorage(uuid, file)
                except:
                    traceback.print_exc()
                    print 'error processing file - {file}'.format(file=file.file)
                    file.status.state = 'publish'
                    self.updateStorage(uuid, file)

            time.sleep(60)
