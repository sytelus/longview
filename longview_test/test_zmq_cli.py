import longview as lv

def on_event(obj):
    print(obj)

lv.set_debug_verbosity(10)
sub = lv.ZmqPubSub.Subscription(40859, "Topic1", on_event)
print("subscriber is waiting")
lv.wait_key()