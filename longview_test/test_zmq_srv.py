import add_parent_path
import longview as lv
import time

pub = lv.ZmqPubSub.Publication(port = 40859)

for i in range(10000):
    pub.send_obj({'a': i}, "Topic1")
    print("sent ", i)
    time.sleep(1)
