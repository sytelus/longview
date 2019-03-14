import random
from . import utils
import scipy.spatial.distance
import heapq

def pyt_tensor2np(pyt_tensor, convert_scaler=True):
    if pyt_tensor is None:
        return None
    n = pyt_tensor.numpy()
    if len(n.shape) == 1:
        return n[0]
    else:
        return n

def pyt_tuple2np(pyt_tuple):
    return tuple((pyt_tensor2np(t) for t in pyt_tuple))

def pyt_ds2list(pyt_ds):
    pyt_dss = utils.to_array_like(pyt_ds)
    return [pyt_tuple2np(t) for pyt_ds in pyt_dss for t in pyt_ds]

def sample_by_class(data, n_samples, class_col=1, shuffle=True):
    if shuffle:
        random.shuffle(data)
    samples = {}
    for i, t in enumerate(data):
        cls = t[class_col]
        if cls not in samples:
            samples[cls] = []
        if len(samples[cls]) < n_samples:
            samples[cls].append(data[i])
    samples = sum(samples.values(), [])
    return samples

def col2array(dataset, col):
    return [row[col] for row in dataset]

def search_similar(input, compare_to, algorithm='euclidean', topk=5):
    scores = scipy.spatial.distance.cdist(input, com_to, algorithm)
    result = []
    for score, data in zip(scores, compre_to):
        if len(result) < topk:
            heapq.heappush(result, (score, data))
        else:
            heapq.heappushpop(result, (score, data))
    return result