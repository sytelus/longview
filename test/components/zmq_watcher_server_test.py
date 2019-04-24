from tensorwatch.zmq_watcher_server import ZmqWatcherServer
import time

from tensorwatch.v2 import utils
utils.set_debug_verbosity(10)


def main():
    watcher = ZmqWatcherServer()

    for i in range(5000):
        watcher.observe(x=i)
        # print(i)
        time.sleep(1)

main()
