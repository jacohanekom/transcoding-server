__author__ = 'jacohanekom'

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import config
from interface import rpcInterface
from handbrake import handbrakeThread
from publish import publishThread
from metadata import metadataThread

print "Starting RPC Server {interface} - {port}".format(
    interface=config.RPC_LISTENING_INTERFACE,
    port=config.RPC_PORT
)
# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = (config.RPC_PATH,)

#setup storage
storage = dict()

# Create server
server = SimpleXMLRPCServer((config.RPC_LISTENING_INTERFACE, config.RPC_PORT), requestHandler=RequestHandler)
server.register_introspection_functions()
server.register_instance(rpcInterface(storage))

#starting handbrake thread
handbrake = handbrakeThread(storage)
handbrake.start()

#starting publisher thread
metadata = metadataThread(storage)
metadata.start()

#starting the publisher thread
publisher = publishThread(storage)
publisher.start()

# Run the server's main loop
server.serve_forever()