import tensorwatch as tw
import time
from tensorwatch.zmq_wrapper import ZmqPubSub
from tensorwatch import utils

utils.set_debug_verbosity(10)

def clisrv_callback(clisrv, msg):
    print(msg)

stream = ZmqPubSub.Publication(port = 40859)
clisrv = ZmqPubSub.ClientServer(40860, True, clisrv_callback)

for i in range(10000):
    stream.send_obj({'a': i}, "Topic1")
    print("sent ", i)
    time.sleep(1)
