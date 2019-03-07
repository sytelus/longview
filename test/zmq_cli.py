import tensorwatch as tw
import time
from tensorwatch.zmq_pub_sub import ZmqPubSub
from tensorwatch import utils

def on_event(obj):
    print(obj)

utils.set_debug_verbosity(10)
sub = ZmqPubSub.Subscription(40859, "Topic1", on_event)
print("subscriber is waiting")

clisrv = ZmqPubSub.ClientServer(40860, False)
clisrv.send_obj("hello 1")
print('sleeping..')
time.sleep(10)
clisrv.send_obj("hello 2")

print('waiting for key..')
utils.wait_key()