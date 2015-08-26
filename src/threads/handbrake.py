import threading, sys
import time
import os
import subprocess
import tempfile
import config
import utils

class HandbrakeThread(utils.Thread):
    level = 0

    def run(self):
        while True:
            for uuid in self.getAvailableFiles():
                file = self.getStorage(uuid)

                try:
                    success = False
                    start = time.time()

                    file.status.state = self.get_status(1)
                    self.updateStorage(uuid, file)

                    output = os.path.join(tempfile.gettempdir(), uuid + config.HANDBRAKE_EXTENSION)
                    cmd = [config.HANDBRAKE_CLI_PATH, '-i', file.file, '-o', output, '--preset={profile}'.
                        format(profile=config.HANDBRAKE_PRESET)]
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
                    while True:
                        out = proc.stdout.readline()
                        content = repr(out)
                        if 'fps' in content and 'ETA' in content:
                            file.status.percent = content.split(',', 2)[1].split('%')[0].strip()
                            file.status.fps = content.split(',')[1].split('(')[1].replace('fps', '').strip()
                            file.status.time = time.time() - start
                            self.updateStorage(uuid, file)

                        if 'Encode done' in content:
                            file.status.state = self.get_status(2)
                            file.status.percent = '100'
                            self.updateStorage(uuid, file)
                            break

                        if 'HandBrake has exited.' in content:
                            file.status.state = self.get_status(3)
                            self.updateStorage(uuid, file)
                            break
                except:
                    file.status.state = self.get_status(3,sys.exc_info()[0])
                    self.updateStorage(uuid, file)
            time.sleep(60)
