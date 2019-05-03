from tensorwatch.zmq_watcher_client import ZmqWatcherClient
import time

from tensorwatch import utils
utils.set_debug_verbosity(10)


def main():
    watcher = ZmqWatcherClient()
    stream = watcher.get_stream(expr='lambda vars:vars.x**2')
    stream.console_debug = True
    input('pause')

main()

