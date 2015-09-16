__author__ = 'jacohanekom'
RPC_PORT = 8000
RPC_LISTENING_INTERFACE = '0.0.0.0'
RPC_PATH = '/handbrake'
MODES = ['threads.HandbrakeThread', 'threads.MetadataThread','threads.PublishThread', 'threads.NotifierThread']

HANDBRAKE_CLI_PATH = '/usr/bin/HandBrakeCLI'
HANDBRAKE_PRESET = 'AppleTV 3'
HANDBRAKE_EXTENSION = '.m4v'
HANDBRAKE_SUPPORTED_FILES = [".mkv",".mp4",".avi",".wmv", ".m4v"]
HANDBRAKE_MIN_SIZE=100048576

METADATA_ATOMIC_PARSLEY = '/usr/bin/AtomicParsley'
METADATA_TUMBLR_KEY = 'g0AZxEgfC9IBIiMlP4JcKoS0uXpGh8GATbqmiqwakKIZA2meNe'
METADATA_MOVIE_KEY = '24318688f151a0bbdc3042c313b35244'

PUBLISH_MOUNTS = {'/media/media_a_g': '0-71','/media/media_h_q': '73-81','/media/media_r_s': '82-83', '/media/media_t_z':'84-127'}
PUBLISH_MOVIES_FOLDER = 'Movies'
PUBLISH_TVSHOWS_FOLDER = 'TV Shows'

NOTIFIER_SICKBEARD_DATABASE_PATH = '/home/jhanekom/Applications/SickRage/sickbeard.db'
NOTIFIER_PLEX_HOST = '127.0.0.1'
NOTIFIER_PLEX_PORT = '32400'

NOTIFIER_COUCHPOTATO_URL = 'http://127.0.0.1/couchpotato/'
NOTIFIER_COUCHPOTATO_KEY = '716e4e6d9d764d8cafb6bf46cf4f2dd2'