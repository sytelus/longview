import tensorwatch as tw

from regim import *
ds = DataUtils.mnist_datasets(linearize=True, train_test=False)
ds = DataUtils.sample_by_class(ds, k=5, shuffle=True, as_np=True, no_test=True)

comps = tw.get_tsne_components(ds, col=0)