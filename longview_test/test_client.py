import longview as lv
import time
import math

def show_find_lr():
    cli_train = lv.WatchClient()
    plot = lv.LinePlot()
    
    train_batch_loss = cli_train.create_stream('batch', 'map(lambda d:(d.tt.scheduler.get_lr()[0], d.metrics.batch_loss), l)')
    plot.show(train_batch_loss, xlabel='Epoch', ylabel='Loss')
    
    lv.wait_key()


def show_dlc_output():
    cli = cli_train = lv.WatchClient()
    #cli = lv.WatchClient()
    
    imgs = cli.create_stream('batch', 
        "top(regim_extract, l, out_xform=pyt_img_img_out_xform, group_key=lambda x:'', topk=10, order='rnd')", throttle=3)
    img_plot = lv.ImagePlot()
    img_plot.show(imgs, img_width=39, img_height=69)

    lv.wait_key()

def show_worst_in_class():
    cli_train = lv.WatchClient()
    cli = lv.WatchClient()


    imgs = cli.create_stream('batch', 
        'top(regim_extract, l, out_xform=pyt_img_cl_out_xform)', throttle=3)
    img_plot = lv.ImagePlot()
    img_plot.show(imgs)

    lv.wait_key()

def show_mnist_grads_test():
    train_cli = lv.WatchClient()

    grads = train_cli.create_stream('batch', 'map(lambda d:avg_abs_grads(d.model), l)', throttle=3)
    grad_plot = lv.LinePlot()
    grad_plot.show(grads, xlabel='Epoch', ylabel='Gradients', redraw_after=0, keep_old=20, dim_old=True)

    lv.wait_key()

def show_mnist_epoch_loss_acc_test():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.LinePlot()

    train_loss = train_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_loss, l)')
    plot.show(train_loss, xlabel='Epoch', ylabel='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_accuracy, l)')
    plot.show(test_acc, xlabel='Epoch', ylabel='Test Accuracy', ylim=(0,1))


def show_mnist_batch_loss_acc_test():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.LinePlot()

    train_loss = train_cli.create_stream("batch", 'map(lambda v:v.loss, l)')
    plot.show(train_loss, xlabel='Epoch', ylabel='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_accuracy, l)')
    plot.show(test_acc, xlabel='Epoch', ylabel='Test Accuracy')

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

show_mnist_epoch_loss_acc_test()
show_find_lr()
show_dlc_output()
show_worst_in_class()
show_mnist_grads_test()
show_graph_test()
read_stream_test()  
show_stream_test()



