import tensorwatch as tw
import objgraph, time #pip install objgraph

cli = tw.RemoteWatcherClient()
time.sleep(10)
del cli

import gc
gc.collect()

import time
time.sleep(2)

objgraph.show_backrefs(objgraph.by_type('RemoteWatcherClient'), refcounts=True, filename='b.png')

