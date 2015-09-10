__author__ = 'jacohanekom'
RPC_PORT = 8000
RPC_LISTENING_INTERFACE = 'localhost'
RPC_PATH = '/handbrake'
MODES = ['threads.HandbrakeThread', 'threads.MetadataThread','threads.PublishThread', 'threads.NotifierThread']

HANDBRAKE_CLI_PATH = '/usr/local/bin/HandBrakeCLI'
HANDBRAKE_PRESET = 'AppleTV 3'
HANDBRAKE_EXTENSION = '.m4v'
HANDBRAKE_SUPPORTED_FILES = [".mkv",".mp4",".avi",".wmv", ".m4v"]
HANDBRAKE_MIN_SIZE=100048576
#HANDBRAKE_MIN_SIZE=100

METADATA_ATOMIC_PARSLEY = '/usr/local/bin/AtomicParsley'
METADATA_TUMBLR_KEY = 'g0AZxEgfC9IBIiMlP4JcKoS0uXpGh8GATbqmiqwakKIZA2meNe'
METADATA_MOVIE_KEY = '24318688f151a0bbdc3042c313b35244'

PUBLISH_MOUNTS = {'/Volumes/MEDIA (A-G)': '0-71','/Volumes/MEDIA (H-Q)': '73-81','/Volumes/MEDIA (R-S)': '82-83', '/Volumes/MEDIA (T-Z)':'84-127'}
#PUBLISH_MOUNTS = {'/Users/jacohanekom/Volumes/MEDIA (A-H)': '0-72','/Users/jacohanekom/Volumes/MEDIA (I-Q)': '73-81',
#                  '/Users/jacohanekom/Volumes/MEDIA (R-Z)': '82-127'}
PUBLISH_MOVIES_FOLDER = 'Movies'
PUBLISH_TVSHOWS_FOLDER = 'TV Shows'

NOTIFIER_SICKBEARD_DATABASE_PATH = '/Applications/SickRage/sickbeard.db'

