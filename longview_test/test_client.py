import longview as lv
import time
import math

def show_stream_test():
    cli = lv.WatchClient()

    s1 = cli.create_stream("LossEvent", 'map(lambda v:math.sqrt(v.loss), l)')
    r1 = lv.ScatterTextRenderer('L1')
    r1.show(s1)

    s2 = cli.create_stream("Loss2Event", 'map(lambda v:v.loss2*v.loss2, l)')
    r2 = lv.ScatterTextRenderer('L2')
    r2.show(s2)
    
    lv.wait_key()

def read_stream_test():
    cli = lv.WatchClient()

    with cli.create_stream("Loss2Event", 'map(lambda v:math.sqrt(v.loss2), l)') as s1:
        for eval_result in s1:
            print(eval_result.result)
    print('done')
    lv.wait_key()

read_stream_test()  
show_stream_test()



