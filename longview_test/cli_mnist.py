import longview as lv
import time
import math
from longview import utils

utils.set_debug_verbosity(4)


def show_find_lr():
    cli_train = lv.WatchClient()
    plot = lv.mpl.LinePlot()
    
    train_batch_loss = cli_train.create_stream('batch', 'map(lambda d:(d.tt.scheduler.get_lr()[0], d.metrics.batch_loss), l)')
    plot.show(train_batch_loss, xtitle='Epoch', ytitle='Loss')
    
    utils.wait_ley()

def worst_in_class():
    cli_train = lv.WatchClient()
    cli = lv.WatchClient()

    imgs = cli_train.create_stream('batch', 
        'top(l, out_xform=pyt_img_class_out_xform)', throttle=1)
    img_plot = lv.mpl.ImagePlot()
    img_plot.show(imgs)

    utils.wait_ley()

def plot_grads():
    train_cli = lv.WatchClient()
    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    p = lv.plotly.ArrayPlot('Demo')
    p.add(grads, xtitle='Epoch', ytitle='Gradients', history_len=30, new_on_eval=True)

def plot_grads1():
    train_cli = lv.WatchClient()

    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    grad_plot = lv.mpl.LinePlot()
    grad_plot.show(grads, xtitle='Epoch', ytitle='Gradients', clear_after_each=1, history_len=40, dim_history=True)

    utils.wait_ley()

def plot_weight():
    train_cli = lv.WatchClient()

    params = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.abs().mean().item()), l)', throttle=1)
    params_plot = lv.mpl.LinePlot()
    params_plot.show(params, xtitle='Epoch', ytitle='avg |params|', clear_after_each=1, history_len=40, dim_history=True)

    utils.wait_ley()

def epoch_stats():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.mpl.LinePlot()

    train_loss = train_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_loss, l)')
    plot.show(train_loss, xtitle='Epoch', ytitle='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_accuracy, l)')
    plot.show(test_acc, xtitle='Epoch', ytitle='Test Accuracy', yrange=(0,1))


def batch_stats():
    train_cli = lv.WatchClient()
    test_cli = lv.WatchClient()

    plot = lv.mpl.LinePlot()

    train_loss = train_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_loss, l)')
    plot.show(train_loss, xtitle='Epoch', ytitle='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_accuracy, l)')
    plot.show(test_acc, xtitle='Epoch', ytitle='Test Accuracy')
