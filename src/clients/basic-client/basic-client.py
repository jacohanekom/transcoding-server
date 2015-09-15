import os, xmlrpclib, subprocess, fnmatch, sys

TRANSCODING_SERVER_URL = 'http://localhost:8000/handbrake'
WATCH_PATH = '/home/jhanekom/Downloads/complete'

def extract_rar(path):
    test_proc = subprocess.Popen(['unrar', 't', path], stdout=subprocess.PIPE)
    staging_files = []
    files = []
    clean_files = False

    while True:
        out = test_proc.stdout.readline()

        if 'All OK' in repr(out):
            [files.append(item) for item in staging_files if item not in files]
            break
        elif 'Testing archive' in repr(out):
            staging_files.append(repr(out).replace('Testing archive ','')[1:-3])
        elif 'Total errors' in repr(out):
            break

    if files:
        extract_proc = subprocess.Popen(['unrar', 'e', '-y', path, os.path.split(path)[0]], stdout=subprocess.PIPE)
        while True:
            out = extract_proc.stdout.readline()

            if 'All OK' in repr(out):
                clean_files = True
                break

    if clean_files:
        for rar_file in files:
	    os.remove(rar_file)


if __name__ == "__main__":
    for root, dirnames, filenames in os.walk(WATCH_PATH):
        for filename in fnmatch.filter(filenames, '*.rar'):
            if os.path.isfile(os.path.join(root, filename)):
                extract_rar(os.path.join(root, filename))

    s = xmlrpclib.ServerProxy(TRANSCODING_SERVER_URL, allow_none=True)
    for root, dirnames, filenames in os.walk(WATCH_PATH):
        for filename in fnmatch.filter(filenames, '*'):
            file = os.path.join(root, filename).replace(WATCH_PATH,'')
            if file.endswith("rar"):
                continue

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
