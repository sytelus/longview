from itertools import *

def skip_mod(mod, g):
    for index, item in enumerate(g):
        if index % mod == 0:
            yield item

def groupby2(l, key=lambda x:x, val=lambda x:x, agg=lambda x:x, sort=True):
    if sort:
        l = sorted(l, key=key)
    return ((k, agg((val(x) for x in v))) \
        for k,v in itertools.groupby(l, key=key))

def avg_abs_grads(model, weight_or_bias=True):
    for i, (n, p) in enumerate(model.named_parameters()):
        if p.requires_grad:
            is_bias = 'bias' in n
            if (weight_or_bias and not is_bias) or (not weight_or_bias and is_bias):
                yield i, p.grad.abs().mean().item(), n

def worst_in_class(t_f, l):
    min_t = {}
    for t in l:
        input, output, label, loss = t_f(l)
        # each batch, get tuple
        f = zip(input, output, label, loss)
        # group by class
        by_class = groupby2(f, lambda t: t[2])
        # pick the first value for each class
        s = (islice(sorted(v, lambda t: t[3]), 1) for label, v in by_class)
        changed = False
        for i,o,lb,ls in s:
            cur_min = min_t.get(lb, None)
            if cur_min is None or (ls is not None and cur_min[2] < ls):
                min_t[lb] = (i,o,lb,ls)
                changed = True
        if changed:
            yield min_t.values()

