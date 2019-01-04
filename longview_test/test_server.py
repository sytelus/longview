import longview as lv
import time

srv = lv.WatchServer()

for i in range(100):
    srv.log_event("LossEvent", loss=i)
    print('sent loss ', i)
    time.sleep(1)
    for j in range(3):
        srv.log_event("Loss2Event", loss2=j)
        print('sent loss2 ', j)
        time.sleep(1)
    srv.end_event("Loss2Event")
srv.end_event("Loss1Event")