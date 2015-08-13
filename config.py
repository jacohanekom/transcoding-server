__author__ = 'jacohanekom'
RPC_PORT = 8000
RPC_LISTENING_INTERFACE = 'localhost'
RPC_PATH = '/handbrake'
HANDBRAKE_ENABLED = True
HANDBRAKE_CLI_PATH = '/usr/local/bin/HandBrakeCLI'
HANDBRAKE_PRESET = 'AppleTV 3'
HANDBRAKE_EXTENSION = '.m4v'
METADATA_EMBEDDING_ENABLED = True
METADATA_ATOMIC_PARSLEY = '/usr/local/bin/AtomicParsley'
METADATA_TUMBLR_KEY = 'g0AZxEgfC9IBIiMlP4JcKoS0uXpGh8GATbqmiqwakKIZA2meNe'
METADATA_MOVIE_KEY = '24318688f151a0bbdc3042c313b35244'
PUBLISH_MOUNTS = {'/Volumes/MEDIA (A-H)': '0-72',
 '/Volumes/MEDIA (I-Q)': '73-81',
 '/Volumes/MEDIA (R-Z)': '82-127'}
PUBLISH_MOVIES_FOLDER = 'Movies'
PUBLISH_TVSHOWS_FOLDER = 'TV Shows'
SICKBEARD_ENABLED = True
SICKBEARD_HOST = '192.168.0.2'
SICKBEARD_PORT = 8081
SICKBEARD_HTTP_FOLDER = 'sickbeard'
SICKBEARD_API_KEY = 'a9d23c7cec791fd77d4f9367096983ed'
COUCHPOTATO_ENABLED = True
COUCHPOTATO_HOST = '192.168.0.2'
COUCHPOTATO_PORT = 5050
COUCHPOTATO_HTTP_FOLDER = 'couchpotato'
COUCHPOTATO_API_KEY = '493fe37447ca4ed58385cfb2f66ce60f'
HANDBRAKE_SUPPORTED_FILES = [".mkv",".mp4",".avi",".wmv"]
HANDBRAKE_MIN_SIZE=100048576
