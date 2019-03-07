import tensorwatch as tw
import time
import math
from tensorwatch import utils

utils.set_debug_verbosity(4)


def show_find_lr():
    cli_train = tw.WatchClient()
    plot = tw.mpl.LinePlot()
    
    train_batch_loss = cli_train.create_stream('batch', 'map(lambda d:(d.tt.scheduler.get_lr()[0], d.metrics.batch_loss), l)')
    plot.show(train_batch_loss, xtitle='Epoch', ytitle='Loss')
    
    utils.wait_ley()

def img_in_class():
    cli_train = tw.WatchClient()

    imgs = cli_train.create_stream('batch', 
        "top(l, out_xform=pyt_img_class_out_xform, order='rnd')", throttle=1)
    img_plot = tw.mpl.ImagePlot()
    img_plot.add(imgs)
    img_plot.show()

    utils.wait_ley()

def plot_grads():
    train_cli = tw.WatchClient()
    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    p = tw.plotly.ArrayPlot('Demo')
    p.add(grads, xtitle='Epoch', ytitle='Gradients', history_len=30, new_on_eval=True)

def plot_grads1():
    train_cli = tw.WatchClient()

    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    grad_plot = tw.mpl.LinePlot()
    grad_plot.show(grads, xtitle='Epoch', ytitle='Gradients', clear_after_each=1, history_len=40, dim_history=True)

    utils.wait_ley()

def plot_weight():
    train_cli = tw.WatchClient()

    params = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.abs().mean().item()), l)', throttle=1)
    params_plot = tw.mpl.LinePlot()
    params_plot.show(params, xtitle='Epoch', ytitle='avg |params|', clear_after_each=1, history_len=40, dim_history=True)

    utils.wait_ley()

def epoch_stats():
    train_cli = tw.WatchClient()
    test_cli = tw.WatchClient()

    plot = tw.mpl.LinePlot()

    train_loss = train_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_loss, l)')
    plot.show(train_loss, xtitle='Epoch', ytitle='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_accuracy, l)')
    plot.show(test_acc, xtitle='Epoch', ytitle='Test Accuracy', yrange=(0,1))


def batch_stats():
    train_cli = tw.WatchClient()
    test_cli = tw.WatchClient()

    plot = tw.mpl.LinePlot()

    train_loss = train_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_loss, l)')
    plot.show(train_loss, xtitle='Epoch', ytitle='Train Loss', final_show=False)
    
    test_acc = test_cli.create_stream("batch", 'map(lambda v:v.metrics.batch_accuracy, l)')
    plot.show(test_acc, xtitle='Epoch', ytitle='Test Accuracy')

img_in_class()