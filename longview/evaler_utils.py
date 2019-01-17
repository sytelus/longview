from itertools import *
import torch
import math

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
    return(input, "T:{},Pb:{:4f},pd:{},L:{:4f}".format(truth, math.exp(output[0]), output[1], loss))

def pyt_in_xform(t):
    input, output, truth, loss = t
    return (input, output, truth.item(), loss.item())

def regim_extract(batch_data):
    input, output, truth, loss = \
        batch_data.input, batch_data.output, batch_data.label, batch_data.loss_all
    # each batch item, get tuple
    flattened = (pyt_in_xform(t) for t in \
        zip(input, output, truth, loss))
    return flattened

def top(extract_f, l, topk=1, descending=True, group_key=None, out_xform=lambda x:x):
    min_result = {}
    for batch_data in l:
        flattened = extract_f(batch_data)
        # group by class - by default group by truth value
        group_key = group_key or (lambda t: t[2])
        by_class = groupby2(flattened, group_key)
        # pick the first values for each class after sorting by loss
        s = (islice(sorted(v, key=lambda t: t[3], reverse=descending), topk) for label, v in by_class)
        changed = False
        for si in s:
            for i,o,tr,ls in si:
                key = group_key((i,o,tr,ls))
                cur_min = min_result.get(key, None)
                if cur_min is None or (ls is not None and cur_min[3] < ls):
                    min_result[key] = (i,o,tr,ls)
                    changed = True
        if changed:
            yield (out_xform(t) for t in min_result.values())


