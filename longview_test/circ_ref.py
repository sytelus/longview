import longview as lv
import objgraph, time

cli = lv.WatchClient()
time.sleep(10)
del cli

import gc
gc.collect()

import time
time.sleep(2)

objgraph.show_backrefs(objgraph.by_type('WatchClient'), refcounts=True, filename='b.png')
