import longview as lv
import time
import math

def show_find_lr():
    cli_train = lv.WatchClient()
    plot = lv.LinePlot()
    
    train_batch_loss = cli_train.create_stream('batch', 'map(lambda d:(d.tt.scheduler.get_lr()[0], d.metrics.batch_loss), l)')
    plot.show(train_batch_loss, xlabel='Epoch', ylabel='Loss')
    
    lv.wait_key()

def dlc_show_rand_outputs():
    cli = cli_train = lv.WatchClient()
    #cli = lv.WatchClient()
    
    imgs = cli.create_stream('batch', 
        "top(l, out_xform=pyt_img_img_out_xform, group_key=lambda x:'', topk=10, order='rnd')", 
        throttle=1)
    img_plot = lv.ImagePlot()
    img_plot.show(imgs, img_width=39, img_height=69, viz_img_scale=10)

    lv.wait_key()

def mnist_worst_in_class():
    cli_train = lv.WatchClient()
    cli = lv.WatchClient()


    imgs = cli_train.create_stream('batch', 
        'top(l, out_xform=pyt_img_class_out_xform)', throttle=1)
    img_plot = lv.ImagePlot()
    img_plot.show(imgs)

    lv.wait_key()

def mnist_plot_grads():
    train_cli = lv.WatchClient()

    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    grad_plot = lv.LinePlot()
    grad_plot.show(grads, xlabel='Epoch', ylabel='Gradients', redraw_after=0, keep_old=40, dim_old=True)

    lv.wait_key()

def mnist_plot_weight():
    train_cli = lv.WatchClient()

    params = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.abs().mean().item()), l)', throttle=1)
    params_plot = lv.LinePlot()
    params_plot.show(params, xlabel='Epoch', ylabel='avg |params|', redraw_after=0, keep_old=40, dim_old=True)

    lv.wait_key()

def mnist_show_epoch_stats():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.LinePlot()

    train_loss = train_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_loss, l)')
    plot.show(train_loss, xlabel='Epoch', ylabel='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_accuracy, l)')
    plot.show(test_acc, xlabel='Epoch', ylabel='Test Accuracy', ylim=(0,1))


def mnist_show_batch_stats():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.LinePlot()

    train_loss = train_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_loss, l)')
    plot.show(train_loss, xlabel='Epoch', ylabel='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_accuracy, l)')
    plot.show(test_acc, xlabel='Epoch', ylabel='Test Accuracy')

def basic_show_graph():
    cli = lv.WatchClient()

    plot = lv.LinePlot()

    s1 = cli.create_stream("LossEvent", 'map(lambda v:math.sqrt(v.loss), l)')
    plot.show(s1, 'i', 'sl', 'SqrtLoss', False)

    s2 = cli.create_stream("Loss2Event", 'map(lambda v:v.loss2*v.loss2, l)')
    plot.show(s2, 'i', 'l', 'Loss2')


def basic_show_stream():
    cli = lv.WatchClient()

    s1 = cli.create_stream("LossEvent", 'map(lambda v:math.sqrt(v.loss), l)')
    r1 = lv.TextPrinter('L1')
    r1.show(s1)

    s2 = cli.create_stream("Loss2Event", 'map(lambda v:v.loss2*v.loss2, l)')
    r2 = lv.TextPrinter('L2')
    r2.show(s2)
    
    lv.wait_key()

def basic_read_stream():
    cli = lv.WatchClient()

    with cli.create_stream("Loss2Event", 'map(lambda v:math.sqrt(v.loss2), l)') as s1:
        for eval_result in s1:
            print(eval_result.result)
    print('done')
    lv.wait_key()

dlc_show_rand_outputs()
show_find_lr()
mnist_show_batch_stats()
mnist_show_epoch_stats()
mnist_plot_grads()
mnist_plot_weight()
mnist_worst_in_class()

basic_read_stream()  
basic_show_graph()
basic_show_stream()



