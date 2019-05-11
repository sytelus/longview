import numpy as np
import torch
import math
import random
from . import utils
from .lv_types import ImagePlotItem
from collections import OrderedDict

def skip_mod(mod, g):
    for index, item in enumerate(g):
        if index % mod == 0:
            yield item

# sort keys, group by key, apply val function to each value in group, aggregate values
def groupby2(l, key=lambda x:x, val=lambda x:x, agg=lambda x:x, sort=True):
    if sort:
        l = sorted(l, key=key)
    grp = ((k,v) for k,v in groupby(l, key=key))
    valx = ((k, (val(x) for x in v)) for k,v in grp)
    aggx = ((k, agg(v)) for k,v in valx)
    return aggx

# aggregate weights or biases, use p2v to transform tensor to scaler
def agg_params(model, p2v, weight_or_bias=True):
    for i, (n, p) in enumerate(model.named_parameters()):
        if p.requires_grad:
            is_bias = 'bias' in n
            if (weight_or_bias and not is_bias) or (not weight_or_bias and is_bias):
                yield i, p2v(p), n

# use this for image to class problems
def pyt_img_class_out_xform(item): # (input_val, target, in_weight, out_weight, output_val, loss)
    input_val = item[0].data.cpu().numpy()
    # turn log-probabilities in to (max log-probability, class ID)
    output_val = torch.max(item[4],0)
    # return image, text
    return ImagePlotItem((input_val,), title="T:{},Pb:{:.2f},pd:{:.2f},L:{:.2f}".\
        format(item[1], math.exp(output_val[0]), output_val[1], item[5]))

# use this for image to image translation problems
def pyt_img_img_out_xform(item): # (input_val, target, in_weight, out_weight, output_val, loss)
    input_val = item[0].data.cpu().numpy()
    output_val = item[4].data.cpu().numpy()
    target = item[1].data.cpu().numpy()
    tar_weight = item[3].data.cpu().numpy() if item[3] is not None else None

    # return in-image, text, out-image, target-image
    return ImagePlotItem((input_val, target, output_val, tar_weight),
                      title="L:{:.2f}, S:{:.2f}, {:.2f}-{:.2f}, {:.2f}-{:.2f}".\
                          format(item[5], input_val.std(), input_val.min(), input_val.max(), output_val.min(), output_val.max()))

def cols2rows(batch):
    in_weight = utils.fill_like(batch.in_weight, batch.input_val)
    tar_weight = utils.fill_like(batch.tar_weight, batch.input_val)
    losses = [l.mean() for l in batch.loss_all]
    targets = [t.item() if len(t.shape)==0 else t for t in batch.target]

    return list(zip(batch.input_val, targets, in_weight, tar_weight,
               batch.output_val, losses))

def top(l, topk=1, order='dsc', group_key=None, out_xform=lambda x:x):
    min_result = OrderedDict()
    for event_vars in l:
        batch = cols2rows(event_vars.batch)
        # by default group items in batch by target value
        group_key = group_key or (lambda b: b[1]) #target
        by_class = groupby2(batch, group_key)

        # pick the first values for each class after sorting by loss
        reverse, sf, ls_cmp = True, lambda b: b[5], False
        if order=='asc':
            reverse = False
        elif order=='rnd':
            ls_cmp, sf = True, lambda t: random.random()
        elif order=='dsc':
            pass
        else:
            raise ValueError('order parameter must be dsc, asc or rnd')

        # sort grouped objects by sort function then
        # take first k values in each group
        # create (key, topk-sized list) tuples for each group
        s = ((k, list(islice(sorted(v, key=sf, reverse=reverse), topk))) \
           for k,v in by_class)

        # for each group, maintain global k values for each keys
        changed = False
        for k,va in s:
            # get global k values for this key, if it doesn't exist
            # then put current in global min
            cur_min = min_result.get(k, None)
            if cur_min is None:
                min_result[k] = va
                changed = True
            else:
                # for each k value in this group, we will compare
                for i, (va_k, cur_k) in enumerate(zip(va, cur_min)):
                    if ls_cmp or (reverse and cur_k[5] < va_k[5]) \
                        or (not reverse and cur_k[5] > va_k[5]):
                        cur_min[i] = va[i]
                        changed = True
        if changed:
            # flatten each list in dictionary value
            yield (out_xform(t) for va in min_result.values() for t in va)


