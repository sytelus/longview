from tensorwatch.remote_watcher_server import RemoteWatcherServer
import time

from tensorwatch import utils
utils.set_debug_verbosity(10)


def main():
    watcher = RemoteWatcherServer()

    for i in range(5000):
        watcher.observe(x=i)
        # print(i)
        time.sleep(1)

main()
