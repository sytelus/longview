from tensorwatch.remote_watcher_client import RemoteWatcherClient
import time

from tensorwatch import utils
utils.set_debug_verbosity(10)


def main():
    watcher = RemoteWatcherClient()
    stream = watcher.create_stream(expr='lambda vars:vars.x**2')
    stream.console_debug = True
    input('pause')

main()

