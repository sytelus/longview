import longview as lv
import time


def on_event(obj):
    print(obj)

lv.set_debug_verbosity(10)
sub = lv.ZmqPubSub.Subscription(40859, "Topic1", on_event)
print("subscriber is waiting")

clisrv = lv.ZmqPubSub.ClientServer(40860, False)
clisrv.send_obj("hello 1")
print('sleeping..')
time.sleep(10)
clisrv.send_obj("hello 2")

print('waiting for key..')
lv.wait_key()