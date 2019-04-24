from tensorwatch.watcher import Watcher
from tensorwatch.publisher import Publisher
from tensorwatch.zmq_publisher import ZmqPublisher
from tensorwatch.zmq_subscriber import ZmqSubscriber

def main():
    watcher = Watcher()
    zmq_pub = ZmqPublisher(name = 'ZmqPub', console_debug=True)
    zmq_sub = ZmqSubscriber(name = 'ZmqSub', console_debug=True)

    pub = watcher.create_stream('lambda vars:vars.x**2', subscribers=[zmq_pub])

    for i in range(5):
        watcher.observe(x=i)
    input('paused')

main()



