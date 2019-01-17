from itertools import *
import torch
import math
import random

def skip_mod(mod, g):
    for index, item in enumerate(g):
        if index % mod == 0:
            yield item

def groupby2(l, key=lambda x:x, val=lambda x:x, agg=lambda x:x, sort=True):
    if sort:
        l = sorted(l, key=key)
        grp = ((k,v) for k,v in groupby(l, key=key))
        valx = ((k, (val(x) for x in v)) for k,v in grp)
        aggx = ((k, agg(v)) for k,v in valx)
    return aggx

def avg_abs_grads(model, weight_or_bias=True):
    for i, (n, p) in enumerate(model.named_parameters()):
        if p.requires_grad:
            is_bias = 'bias' in n
            if (weight_or_bias and not is_bias) or (not weight_or_bias and is_bias):
                yield i, p.grad.abs().mean().item(), n

def pyt_img_cl_out_xform(t):
    input, output, truth, loss = t
    input = input.data.cpu().numpy()
    output = torch.max(output,0)
    return(input, "T:{},Pb:{:4f},pd:{},L:{:4f}".format(truth, math.exp(output[0]), \
       output[1], loss), None, "")

def pyt_img_img_out_xform(t):
    input, output, truth, loss = t
    input = input.data.cpu().numpy()
    output = output.data.cpu().numpy()
    return(input, "L:{:4f}".format(loss), output, "")

def pyt_in_xform(t):
    input, output, truth, loss = t
    return (input, output, truth.item() if len(truth.shape)==0 else truth, loss.item())

def regim_extract(batch_data):
    input, output, truth, loss = \
        batch_data.input, batch_data.output, batch_data.label, batch_data.loss_all

    if len(loss.shape) == 0:
        loss = torch.Tensor((truth.shape[0],)).fill_(loss)
    elif len(loss.shape) > 2 or (len(loss.shape) == 2 and loss.shape[1] > 1):
        loss = [x.mean() for x in loss]

    # each batch item, get tuple
    flattened = (pyt_in_xform(t) for t in \
        zip(input, output, truth, loss))
    return flattened

def top(extract_f, l, topk=1, order='dsc', group_key=None, out_xform=lambda x:x):
    min_result = {}
    for batch_data in l:
        flattened = extract_f(batch_data)
        # group by class - by default group by truth value
        group_key = group_key or (lambda t: t[2])
        by_class = groupby2(flattened, group_key)
        # pick the first values for each class after sorting by loss
        reverse, sf, ls_cmp = True, lambda t: t[3], False
        if order=='asc':
            reverse = False
        elif order=='rnd':
            ls_cmp, sf = True, lambda t: random.random()
        elif order=='dsc':
            pass
        else:
            raise ValueError('order parameter must be dsc, asc or rnd')
        s = ((k, list(islice(sorted(v, key=sf, reverse=reverse), topk))) \
           for k,v in by_class)
        changed = False
        for k,va in s:
            cur_min = min_result.get(k, None)
            if cur_min is None:
                min_result[k] = va
            else:
                for i, ((_,_,_,ls), (_,_,_,lsc)) in enumerate(zip(va, cur_min)):
                    if ls_cmp or lsc < ls:
                        cur_min[i] = va[i]
                        changed = True
        if changed:
            yield (out_xform(t) for t in va for va in min_result.values())


