from tensorwatch.zmq_watcher_client import ZmqWatcherClient
import time

from tensorwatch.v2 import utils
utils.set_debug_verbosity(10)


def main():
    watcher = ZmqWatcherClient()
    publisher = watcher.create_stream('lambda vars:vars.x**2')
    publisher.console_debug = True
    input('pause')

main()

