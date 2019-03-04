import longview as lv
import time
from longview.zmq_pub_sub import ZmqPubSub
from longview import utils

utils.set_debug_verbosity(10)

def clisrv_callback(clisrv, msg):
    print(msg)

pub = ZmqPubSub.Publication(port = 40859)
clisrv = ZmqPubSub.ClientServer(40860, True, clisrv_callback)

for i in range(10000):
    pub.send_obj({'a': i}, "Topic1")
    print("sent ", i)
    time.sleep(1)
