import tensorwatch as tw
import time
import math
from tensorwatch import utils
import matplotlib.pyplot as plt

utils.set_debug_verbosity(4)

def img_in_class():
    cli_train = tw.ZmqWatcherClient()

    imgs = cli_train.create_stream(tw.StreamRequest(event_name='batch',
        expr="top(l, out_xform=pyt_img_class_out_xform, order='rnd')", throttle=1))
    img_plot = tw.mpl.ImagePlot()
    img_plot.add_subscription(imgs, viz_img_scale=3)
    img_plot.show()

    tw.image_utils.plt_loop()

def show_find_lr():
    cli_train = tw.ZmqWatcherClient()
    plot = tw.mpl.LinePlot()
    
    train_batch_loss = cli_train.create_stream('batch', 'map(lambda d:(d.tt.scheduler.get_lr()[0], d.metrics.batch_loss), l)')
    plot.show(train_batch_loss, xtitle='Epoch', ytitle='Loss')
    
    utils.wait_ley()

def plot_grads():
    train_cli = tw.ZmqWatcherClient()
    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    p = tw.plotly.ArrayPlot('Demo')
    p.add(grads, xtitle='Epoch', ytitle='Gradients', history_len=30, new_on_eval=True)

def plot_grads1():
    train_cli = tw.ZmqWatcherClient()

    grads = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.grad.abs().mean().item()), l)', throttle=1)
    grad_plot = tw.mpl.LinePlot()
    grad_plot.show(grads, xtitle='Epoch', ytitle='Gradients', clear_after_each=1, history_len=40, dim_history=True)

    utils.wait_ley()

def plot_weight():
    train_cli = tw.ZmqWatcherClient()

    params = train_cli.create_stream('batch', 'map(lambda d:agg_params(d.model, lambda p: p.abs().mean().item()), l)', throttle=1)
    params_plot = tw.mpl.LinePlot()
    params_plot.add(params, xtitle='Epoch', ytitle='avg |params|', clear_after_each=1, history_len=40, dim_history=True)

    utils.wait_ley()

def epoch_stats():
    train_cli = tw.ZmqWatcherClient()
    test_cli = tw.ZmqWatcherClient()

    plot = tw.mpl.LinePlot()

    train_loss = train_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_loss, l)')
    plot.add(train_loss, xtitle='Epoch', ytitle='Train Loss')
    
    test_acc = test_cli.create_stream("epoch", 'map(lambda v:v.metrics.epoch_accuracy, l)')
    plot.add(test_acc, xtitle='Epoch', ytitle='Test Accuracy', ylim=(0,1))

    plot.show()
    tw.img_util.plt_loop()


def batch_stats():
    plot = tw.mpl.LinePlot()

    train_loss = tw.create_vis('lambda v:(v.metrics.epochf, v.metrics.batch_loss)', 
                         event_name="batch", title='Batch Statistics', throttle=0.75,
                         xtitle='Epoch', ytitle='Train Loss', clear_after_end=False, type='mpl-line')
    
    #train_acc = tw.create_vis('lambda v:(v.metrics.epochf, v.metrics.epoch_loss)', event_name="batch",
    #                     xtitle='Epoch', ytitle='Train Accuracy', clear_after_end=False, yrange=(0,1), 
    #                     vis=train_loss, type='mpl-line')

    train_loss.show()
    tw.image_utils.plt_loop()

def text_stats():
    trl = tw.create_vis('lambda d:(d.x, d.metrics.batch_loss)', event_name='batch', type=None, 
                  xtitle='Epoch', ytitle='Train Loss', clear_after_end=False)
    trl.show()
    input('Paused...')

img_in_class()
#text_stats()
#batch_stats()