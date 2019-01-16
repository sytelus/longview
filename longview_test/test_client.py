import longview as lv
import time
import math

def show_worst_in_class():
    cli_train = lv.WatchClient()
    cli = lv.WatchClient()


    imgs = cli.create_stream('batch', 
        'worst_in_class(lambda d:(d.input, d.output, d.label, d.loss_all), l)', throttle=3)
    img_plot = lv.ImagePlot()
    img_plot.show(imgs)

    lv.wait_key()

def show_mnist_grads_test():
    cli = lv.WatchClient()

    grads = cli.create_stream('batch', 'map(lambda d:avg_abs_grads(d.model), l)', throttle=3)
    grad_plot = lv.LinePlot()
    grad_plot.show(grads, xlabel='Epoch', ylabel='Gradients', redraw_after=0, keep_old=20, dim_old=True)

    lv.wait_key()

def show_mnist_test():
    cli = lv.WatchClient()

    plot = lv.LinePlot()

    s1 = cli.create_stream("batch", 'map(lambda v:math.sqrt(v.loss), l)')
    plot.show(s1, xlabel='i', ylabel='sqrt_loss', label='SqrtLoss', final_show=False)
    
    s1 = cli.create_stream("batch", 'map(lambda v:v.metrics.batch_accuracy, l)')
    plot.show(s1, xlabel='i', ylabel='acc', label='Accuracy')


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

show_worst_in_class()
show_mnist_test()
show_mnist_grads_test()
show_graph_test()
read_stream_test()  
show_stream_test()



