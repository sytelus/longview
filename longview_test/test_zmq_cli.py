import add_parent_path
import longview as lv

def on_event(obj):
    print(obj)

sub = lv.ZmqPubSub.Subscription(40859, "Topic1", on_event)

lv.wait_key()