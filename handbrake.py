import threading, sys
import time
import os
import subprocess
import tempfile
import config

class handbrakeThread(threading.Thread):
    def updateStorage(self, uuid, obj):
        self.registered_files[uuid] = obj

    def getStorage(self, uuid):
        return self.registered_files[uuid]

    def getAvailableFiles(self):
        to_be_processed = list()
        for uuid in self.registered_files:
            if self.registered_files[uuid].status.state == 'Transcoding - Queued':
                to_be_processed.append(uuid)

        return to_be_processed

    def __init__(self, registered_files):
        threading.Thread.__init__(self)
        self.registered_files = registered_files

    def run(self):
        while True:
            for uuid in self.getAvailableFiles():
                file = self.getStorage(uuid)
                
		try:
                	success = False
                	start = time.time()
                	file.status.state = 'Transcoding - Processing'
                	self.updateStorage(uuid, file)
                	output = os.path.join(tempfile.gettempdir(), uuid + config.HANDBRAKE_EXTENSION)
                	cmd = [config.HANDBRAKE_CLI_PATH, '-i', file.file, '-o', output,
                	 	'--preset={profile}'.format(profile=config.HANDBRAKE_PRESET)]
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
                       	 		file.status.state = 'Metadata - Queued'
                        		file.status.percent = '100'
                        		self.updateStorage(uuid, file)
                        		break
                    		
				if 'HandBrake has exited.' in content:
                        		file.status.state = 'Transcoding - Error'
                        		self.updateStorage(uuid, file)
                        		break

		except: 
			file.status.state = 'Transcoding - Error - {error}'.format(error=sys.exc_info()[0])
			self.updateStorage(uuid, file)	
            time.sleep(60)
