import sys
import time
import os
import subprocess
import tempfile
import utils

class HandbrakeThread(utils.Base):
    def run(self):
        print "Starting " + super(HandbrakeThread, self).get_name()

        while True:
            for uuid in super(HandbrakeThread, self).get_available_files():
                file = super(HandbrakeThread, self).get_storage(uuid)

                try:
                    success = False
                    start = time.time()

                    file.status.state = super(HandbrakeThread, self).get_status(1)
                    super(HandbrakeThread, self).update_storage(uuid, file)

                    output = os.path.join(tempfile.gettempdir(), uuid + super(HandbrakeThread, self).get_config()['HANDBRAKE_EXTENSION'])
                    cmd = [super(HandbrakeThread, self).get_config()['HANDBRAKE_CLI_PATH'], '-i', file.file, '-o', output, '--preset={profile}'.
                        format(profile=super(HandbrakeThread, self).get_config()['HANDBRAKE_PRESET'])]
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
                    while True:
                        out = proc.stdout.readline()
                        content = repr(out)
                        if 'fps' in content and 'ETA' in content:
                            file.status.percent = content.split(',', 2)[1].split('%')[0].strip()
                            file.status.fps = content.split(',')[1].split('(')[1].replace('fps', '').strip()
                            file.status.time = time.time() - start
                            super(HandbrakeThread, self).update_storage(uuid, file)

                        if 'Encode done' in content:
                            file.status.state = super(HandbrakeThread, self).get_status(2)
                            file.status.percent = '100'
                            super(HandbrakeThread, self).update_storage(uuid, file)
                            break

                        if 'HandBrake has exited.' in content:
                            file.status.state = super(HandbrakeThread, self).get_status(3)
                            super(HandbrakeThread, self).update_storage(uuid, file)
                            break
                except:
                    file.status.state = super(HandbrakeThread, self).get_status(3,sys.exc_info()[0])
                    super(HandbrakeThread, self).update_storage(uuid, file)
            time.sleep(60)
