from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from . import utils

def _standardize_data(data, col, whitten):
    if col is not None:
        data = [t[col] for t in data]

    #if data is tensor then flatten it first
    if flatten and len(data) > 0 and hasattr(data[0], 'shape') and \
        utils.has_method(data[0], 'reshape'):

        data = [d.reshape((-1,)) for d in data]

    if whitten:
        data = StandardScaler().fit_transform(data)
    return data

def get_tsne_components(data, col=None, whitten=True, n_components=3, perplexity=20, flatten=True):
    data = _standardize_data(data, col, whitten)
    tsne = TSNE(n_components=n_components, perplexity=perplexity)
    tsne_results = tsne.fit_transform(data)
    return tsne_results



