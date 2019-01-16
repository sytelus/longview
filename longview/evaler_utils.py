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

def worst_in_class(t_f, l, topk=1):
    min_t = {}
    for t in l:
        input, output, label, loss = t_f(t)
        # each batch, get tuple
        f = ((i,o,lb.item(),ls.item()) for i,o,lb,ls in \
            zip(input, output, label, loss))
        # group by class
        by_class = groupby2(f, lambda t: t[2])
        # pick the first value for each class after sorting by loss
        s = (islice(sorted(v, key=lambda t: t[3], reverse=True), topk) for label, v in by_class)
        changed = False
        for k in s:
            for i,o,lb,ls in k:
                cur_min = min_t.get(lb, None)
                if cur_min is None or (ls is not None and cur_min[3] < ls):
                    min_t[lb] = (i,o,lb,ls)
                    changed = True
        if changed:
            t = ((v[0].data.cpu().numpy(), torch.max(v[1],0), v[2], v[3]) \
                for v in min_t.values())
            t = ((v[0], "T:{},Pb:{:4f},pd:{},L:{:4f}".format(v[2], math.exp(v[1][0]), v[1][1], v[3])) \
                for v in t)
            yield t

