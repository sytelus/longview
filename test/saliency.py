from tensorwatch.saliency import saliency
from tensorwatch import img_utils, imagenet_utils, pytorch_utils

model = pytorch_utils.get_model('resnet50')
raw_input, input, target_class = pytorch_utils.image_class2tensor('../data/elephant.png', 101,
    image_transform=imagenet_utils.get_image_transform(), image_convert_mode='RGB')
sal = saliency.get_saliency(model, input, target_class)
saliency.show_image_saliency(raw_input, sal)

img_utils.plt_loop()





