from tensorwatch.watcher import Watcher
from tensorwatch.stream import Stream
from tensorwatch.zmq_stream import ZmqStream

def main():
    watcher = Watcher()
    zmq_pub = ZmqStream(for_write=True, stream_name = 'ZmqPub', console_debug=True)
    zmq_sub = ZmqStream(for_write=False, stream_name = 'ZmqSub', console_debug=True)

    stream = watcher.get_stream(expr='lambda vars:vars.x**2')
    zmq_pub.subscribe(stream)

    for i in range(5):
        watcher.observe(x=i)
    input('paused')

main()



