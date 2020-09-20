from gui.battle_control.controllers.arena_border_ctrl import ArenaBorderController

from xfw.events import overrideMethod
import xvm_main.python.config as config
from xvm_main.python.logger import *


COLOR = "0x00FF00"
ALPHA = 100

@overrideMethod(ArenaBorderController, '_ArenaBorderController__getCurrentColor')
def ArenaBorderController__getCurrentColor(base, self, colorBlind):
    # log('ArenaBorderController = %s' % base(self, colorBlind))
    color = int(config.get('battle/borderColor/color', COLOR), 16)
    alpha = int(config.get('battle/borderColor/alpha', ALPHA))
    red = ((color & 0xff0000) >> 16) / 255.0
    green = ((color & 0x00ff00) >> 8) / 255.0
    blue = (color & 0x0000ff) / 255.0
    alpha = alpha / 100.0
    return red, green, blue, alpha

