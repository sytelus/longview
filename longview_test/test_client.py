import longview as lv
import time
import math

def show_graph_test():
    cli = lv.WatchClient()

    plot = lv.LinePlot()

    s1 = cli.create_stream("LossEvent", 'map(lambda v:math.sqrt(v.loss), l)')
    plot.show(s1, 'i', 'sl', 'SqrtLoss', False)

    s2 = cli.create_stream("Loss2Event", 'map(lambda v:v.loss2*v.loss2, l)')
    plot.show(s2, 'i', 'l', 'Loss2')


def show_stream_test():
    cli = lv.WatchClient()

    s1 = cli.create_stream("LossEvent", 'map(lambda v:math.sqrt(v.loss), l)')
    r1 = lv.TextPrinter('L1')
    r1.show(s1)

    s2 = cli.create_stream("Loss2Event", 'map(lambda v:v.loss2*v.loss2, l)')
    r2 = lv.TextPrinter('L2')
    r2.show(s2)
    
    lv.wait_key()

def read_stream_test():
    cli = lv.WatchClient()

    with cli.create_stream("Loss2Event", 'map(lambda v:math.sqrt(v.loss2), l)') as s1:
        for eval_result in s1:
            print(eval_result.result)
    print('done')
    lv.wait_key()

show_graph_test()
read_stream_test()  
show_stream_test()



