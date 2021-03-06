__author__ = 'jacohanekom'
RPC_PORT = 8000
RPC_LISTENING_INTERFACE = '0.0.0.0'
RPC_PATH = '/handbrake'
MODES = ['threads.HandbrakeThread', 'threads.MetadataThread','threads.PublishThread']

HANDBRAKE_CLI_PATH = '/usr/bin/HandBrakeCLI'
HANDBRAKE_PRESET = 'AppleTV 3'
HANDBRAKE_EXTENSION = '.m4v'
HANDBRAKE_SUPPORTED_FILES = [".mkv",".mp4",".avi",".wmv", ".m4v"]
HANDBRAKE_MIN_SIZE=100048576

METADATA_ATOMIC_PARSLEY = '/usr/bin/AtomicParsley'
METADATA_TUMBLR_KEY = 'g0AZxEgfC9IBIiMlP4JcKoS0uXpGh8GATbqmiqwakKIZA2meNe'
METADATA_MOVIE_KEY = '24318688f151a0bbdc3042c313b35244'

PUBLISH_FTP_HOST = '192.168.0.2'
PUBLISH_USER_NAME = 'jhanekom'
PUBLISH_PASSWORD = 'Dell840320@'
PUBLISH_MOUNTS = {'/media/media_a_g': '0-71','/media/media_h_q': '72-81','/media/media_r_s': '82-83', '/media/media_t_z':'84-127'}
PUBLISH_MOVIES_FOLDER = 'Movies'
PUBLISH_TVSHOWS_FOLDER = 'TV Shows'
