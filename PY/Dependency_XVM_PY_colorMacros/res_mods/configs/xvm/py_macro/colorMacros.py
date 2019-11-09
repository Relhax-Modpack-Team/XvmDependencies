from xfw import *
from xvm.utils import hex_to_rgb, rgb_to_hex, smooth_transition_color
from xvm_main.python.logger import *


@xvm.export('dynamic_color')
def _smooth_transition_color(color_100, color_0, percent=None, maximum=100):
    if percent is None:
        return None
    if percent >= maximum:
        return '{:06x}'.format(color_100)
    if percent <= 0:
        return '{:06x}'.format(color_0)
    r_0, g_0, b_0 = hex_to_rgb(color_0)
    r_100, g_100, b_100 = hex_to_rgb(color_100)
    r_delta, g_delta, b_delta = (r_100 - r_0, g_100 - g_0, b_100 - b_0)
    k = percent / float(maximum)
    return '{:06x}'.format(rgb_to_hex(r_0 + int(r_delta * k), g_0 + int(g_delta * k), b_0 + int(b_delta * k)))


@xvm.export('dynamic_colorRGB')
def smooth_transition_colorRGB(color_100, color_0, percent=None, maximum=100):
    if percent is None:
        return None
    else:
        return smooth_transition_color('RGB', color_100, color_0, percent, maximum)


@xvm.export('dynamic_colorRBG')
def smooth_transition_colorRBG(color_100, color_0, percent=None, maximum=100):
    if percent is None:
        return None
    else:
        return smooth_transition_color('RBG', color_100, color_0, percent, maximum)


@xvm.export('dynamic_colorGRB')
def smooth_transition_colorGRB(color_100, color_0, percent=None, maximum=100):
    if percent is None:
        return None
    else:
        return smooth_transition_color('GRB', color_100, color_0, percent, maximum)


@xvm.export('dynamic_colorGBR')
def smooth_transition_colorGBR(color_100, color_0, percent=None, maximum=100):
    if percent is None:
        return None
    else:
        return smooth_transition_color('GBR', color_100, color_0, percent, maximum)


@xvm.export('dynamic_colorBRG')
def smooth_transition_colorBRG(color_100, color_0, percent=None, maximum=100):
    if percent is None:
        return None
    else:
        return smooth_transition_color('BRG', color_100, color_0, percent, maximum)


@xvm.export('dynamic_colorBGR')
def smooth_transition_colorBGR(color_100, color_0, percent=None, maximum=100):
    if percent is None:
        return None
    else:
        return smooth_transition_color('BGR', color_100, color_0, percent, maximum)