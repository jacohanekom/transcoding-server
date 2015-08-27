__author__ = 'jacohanekom'

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import config
from interface import rpcInterface
from threads import HandbrakeThread, MetadataThread, PublishThread, SchedulerThread
import thread

def start_thread(storage, config_dict):
    #module = __import__("threads")
    #class_ = getattr(module, SchedulerThread)

    scheduler = SchedulerThread(storage, config_dict)
    scheduler.run()

if __name__ == '__main__':
    print "Starting RPC Server {interface} - {port}".format(
        interface=config.RPC_LISTENING_INTERFACE,
        port=config.RPC_PORT
    )
    # Restrict to a particular path.
    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = (config.RPC_PATH,)

    # setup storage
    storage = dict()
    config_dict = dict()

    for property, value  in vars(config).iteritems():
        config_dict[property] = value

    #starting all the worker threads
    thread.start_new_thread(start_thread, (storage, config_dict))

    #HandbrakeThread(storage, config_dict).start()
    #MetadataThread(storage, config_dict).start()
    #PublishThread(storage, config_dict).start()

    # Create server
    server = SimpleXMLRPCServer((config.RPC_LISTENING_INTERFACE, config.RPC_PORT), requestHandler=RequestHandler)
    server.register_introspection_functions()
    server.register_instance(rpcInterface(storage))
    server.serve_forever()

print "Server is ready"