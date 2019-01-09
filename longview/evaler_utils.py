
def skip_mod(mod, g):
    for index, item in enumerate(g):
        if index % mod == 0:
            yield item

def avg_abs_grads(model, weight_or_bias=True):
    for i, (n, p) in enumerate(model.named_parameters()):
        if p.requires_grad:
            is_bias = 'bias' in n
            if (weight_or_bias and not is_bias) or (not weight_or_bias and is_bias):
                yield i, p.grad.abs().mean().item(), n