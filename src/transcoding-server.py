__author__ = 'jacohanekom'

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import config
from interface import rpcInterface
from threads import HandbrakeThread, MetadataThread, PublishThread

print "Starting RPC Server {interface} - {port}".format(
    interface=config.RPC_LISTENING_INTERFACE,
    port=config.RPC_PORT
)
# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = (config.RPC_PATH,)

# setup storage
storage = dict()

# Create server
server = SimpleXMLRPCServer((config.RPC_LISTENING_INTERFACE, config.RPC_PORT), requestHandler=RequestHandler)
server.register_introspection_functions()
server.register_instance(rpcInterface(storage))

#starting all the worker threads
HandbrakeThread(storage).start()
MetadataThread(storage).start()
PublishThread(storage).start().start()

# Run the server's main loop
