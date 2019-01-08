
def skip_mod(mod, g):
    for index, item in enumerate(g):
        if index % mod == 0:
            yield item