from tensorwatch.watcher import Watcher
from tensorwatch.stream import Stream
from tensorwatch.zmq_stream_pub import ZmqStreamPub
from tensorwatch.zmq_stream_sub import ZmqStreamSub

def main():
    watcher = Watcher()
    zmq_pub = ZmqStreamPub(name = 'ZmqPub', console_debug=True)
    zmq_sub = ZmqStreamSub(name = 'ZmqSub', console_debug=True)

    stream = watcher.create_stream('lambda vars:vars.x**2', subscribers=[zmq_pub])

    for i in range(5):
        watcher.observe(x=i)
    input('paused')

main()



