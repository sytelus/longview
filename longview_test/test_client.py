import longview as lv
import time
import math

lv.set_debug_verbosity(4)


def show_find_lr():
    cli_train = lv.WatchClient()
    plot = lv.mpl.LinePlot()
    
    train_batch_loss = cli_train.create_stream('batch', 'map(lambda d:(d.tt.scheduler.get_lr()[0], d.metrics.batch_loss), l)')
    plot.show(train_batch_loss, xlabel='Epoch', ylabel='Loss')
    
    lv.wait_key()

def dlc_show_rand_outputs():
    cli = cli_train = lv.WatchClient()
    #cli = lv.WatchClient()
    
    imgs = cli.create_stream('batch', 
        "top(l, out_xform=pyt_img_img_out_xform, group_key=lambda x:'', topk=10, order='rnd')", 
        throttle=1)
    img_plot = lv.mpl.ImagePlot()
    img_plot.show(imgs, img_width=39, img_height=69, viz_img_scale=10)

    lv.wait_key()

def img2img_rnd():
    cli_train = lv.WatchClient()
    cli = lv.WatchClient()

    imgs = cli_train.create_stream('batch', 
        "top(l, out_xform=pyt_img_img_out_xform, group_key=lambda x:'', topk=2, order='rnd')", throttle=1)
    img_plot = lv.mpl.ImagePlot()
    img_plot.show(imgs, img_width=100, img_height=100, viz_img_scale=3, cols=1)

    lv.wait_key()

def mnist_worst_in_class():
    cli_train = lv.WatchClient()
    cli = lv.WatchClient()

    imgs = cli_train.create_stream('batch', 
        'top(l, out_xform=pyt_img_class_out_xform)', throttle=1)
    img_plot = lv.mpl.ImagePlot()
    img_plot.show(imgs)

    lv.wait_key()

def mnist_plot_grads():
    train_cli = lv.WatchClient()
    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    p = lv.plotly.ArrayPlot('Demo')
    p.add(grads, xtitle='Epoch', ytitle='Gradients', history_len=30, new_on_eval=True)

def mnist_plot_grads1():
    train_cli = lv.WatchClient()

    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    grad_plot = lv.mpl.LinePlot()
    grad_plot.show(grads, xlabel='Epoch', ylabel='Gradients', redraw_after=1, keep_old=40, dim_old=True)

    lv.wait_key()

def mnist_plot_weight():
    train_cli = lv.WatchClient()

    params = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.abs().mean().item()), l)', throttle=1)
    params_plot = lv.mpl.LinePlot()
    params_plot.show(params, xlabel='Epoch', ylabel='avg |params|', redraw_after=1, keep_old=40, dim_old=True)

    lv.wait_key()

def mnist_show_epoch_stats():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.mpl.LinePlot()

    train_loss = train_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_loss, l)')
    plot.show(train_loss, xlabel='Epoch', ylabel='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_accuracy, l)')
    plot.show(test_acc, xlabel='Epoch', ylabel='Test Accuracy', ylim=(0,1))


def mnist_show_batch_stats():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.mpl.LinePlot()

    train_loss = train_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_loss, l)')
    plot.show(train_loss, xlabel='Epoch', ylabel='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_accuracy, l)')
    plot.show(test_acc, xlabel='Epoch', ylabel='Test Accuracy')

def basic_show_graph():
    cli = lv.WatchClient()

    plot = lv.mpl.LinePlot()

    s1 = cli.create_stream("ev_i", 'map(lambda v:math.sqrt(v.val), l)')
    plot.show(s1, 'i', 'sl', 'sqrt ev_i', False)

    s2 = cli.create_stream("ev_j", 'map(lambda v:v.val*v.val, l)')
    plot.show(s2, 'i', 'l', 'ev_j')


def basic_show_stream():
    cli = lv.WatchClient()

    print("Subscribing to event ev_i...")
    s1 = cli.create_stream("ev_i", 'map(lambda v:math.sqrt(v.val), l)')
    r1 = lv.TextPrinter('L1')
    r1.show(s1)

    print("Subscribing to event ev_j...")
    s2 = cli.create_stream("ev_j", 'map(lambda v:v.val*v.val, l)')
    r2 = lv.TextPrinter('L2')
    r2.show(s2)
    
    print("Waiting for key...")

    lv.wait_key()

def basic_read_stream():
    cli = lv.WatchClient()

    with cli.create_stream("ev_i", 'map(lambda v:math.sqrt(v.val), l)') as s1:
        for eval_result in s1:
            print(eval_result.result)
    print('done')
    lv.wait_key()

def plotly_line_graph():
    cli = lv.WatchClient()
    s1 = cli.create_stream("ev_i", 'map(lambda v:math.sqrt(v.val), l)')

    p = lv.plotly.LinePlot()
    p.add(s1)
    print(p.figwig)

    lv.wait_key()

def plotly_array_graph():
    cli = lv.WatchClient()
    s1 = cli.create_stream('ev_j', 'map(lambda v:math.sqrt(v.val)*2, l)')

    p = lv.plotly.ArrayPlot('Demo')
    p.add(s1, xtitle='Index', ytitle='sqrt(ev_j)', history_len=3, new_on_end=True)
    lv.wait_key()



########################################################################
mnist_plot_grads()
plotly_array_graph()
plotly_line_graph()

dlc_show_rand_outputs()
img2img_rnd()
show_find_lr()
mnist_show_batch_stats()
mnist_show_epoch_stats()

mnist_plot_weight()
mnist_plot_grads1()
mnist_worst_in_class()

basic_read_stream()  
basic_show_graph()
basic_show_stream()



