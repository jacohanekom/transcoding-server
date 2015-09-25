#!/usr/bin/env python
__author__ = 'jacohanekom'

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import config
from interface import rpcInterface
import thread

def start_thread(name, storage, config_dict):
    module = __import__(name.split(".")[0])
    class_ = getattr(module, name.split(".")[1])
    instance = class_(storage, config_dict)

    instance.run()

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
    thread.start_new_thread(start_thread, ("threads.SchedulerThread", storage, config_dict))

    for cls in config.MODES:
        thread.start_new_thread(start_thread, (cls, storage, config_dict))

    # Create server
    server = SimpleXMLRPCServer((config.RPC_LISTENING_INTERFACE, config.RPC_PORT), requestHandler=RequestHandler, allow_none=True)
    server.register_introspection_functions()
    server.register_instance(rpcInterface(storage, config_dict))
    server.serve_forever()

    print "Server is ready"
