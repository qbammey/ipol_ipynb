import numpy as np

def scb(img, s0=0.015, s1=0.015):
    threshold_0 = np.quantile(img, s0)
    threshold_1 = np.quantile(img, 1-s1)
    img = (img - threshold_0) / (threshold_1 - threshold_0)
    img = np.clip(img, 0, 1)
    return img