from .gradcam import GradCAMExplainer
from .backprop import VanillaGradExplainer, GradxInputExplainer, SaliencyExplainer, \
    IntegrateGradExplainer, DeconvExplainer, GuidedBackpropExplainer, SmoothGradExplainer
from .deeplift import DeepLIFTRescaleExplainer
from .occlusion import OcclusionExplainer
from .epsilon_lrp import EpsilonLrp
import skimage.transform
import torch
from .. import img_utils

def _get_explainer(explainer_name, model, layer_path=None):
    if explainer_name == 'gradcam':
        return GradCAMExplainer(model, target_layer_name_keys=layer_path, use_inp=True)
    if explainer_name == 'vanilla_grad':
        return VanillaGradExplainer(model)
    if explainer_name == 'grad_x_input':
        return GradxInputExplainer(model)
    if explainer_name == 'saliency':
        return SaliencyExplainer(model)
    if explainer_name == 'integrate_grad':
        return IntegrateGradExplainer(model)
    if explainer_name == 'deconv':
        return DeconvExplainer(model)
    if explainer_name == 'guided_backprop':
        return GuidedBackpropExplainer(model)
    if explainer_name == 'smooth_grad':
        return SmoothGradExplainer(model)
    if explainer_name == 'deeplift_rescale':
        return DeepLIFTRescaleExplainer(model)
    if explainer_name == 'occlusion':
        return OcclusionExplainer(model)
    if explainer_name == 'lrp':
        return EpsilonLrp(model)

    raise ValueError('Explainer {} is not recognized'.format(explainer_name))

def get_saliency(model, input, label, method='gradcam', layer_path=['avgpool']):
    exp = _get_explainer(method, model, layer_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    input = input.to(device)
    if label is not None:
        label = label.to(device)

    saliency = exp.explain(input, label)

    saliency = saliency.abs().sum(dim=1)[0].squeeze()
    saliency -= saliency.min()
    saliency /= (saliency.max() + 1e-20)

    return saliency

def show_image_saliency(raw_image, saliency):
    #upsampler = nn.Upsample(size=(raw_image.height, raw_image.width), mode='bilinear')
    saliency_upsampled = skimage.transform.resize(saliency.detach().cpu().numpy(), 
                                                  (raw_image.height, raw_image.width))

    return img_utils.show_image(raw_image, img2=saliency_upsampled, alpha2=0.6, cmap2='jet')
