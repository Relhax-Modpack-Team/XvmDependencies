import BigWorld
import game
import Keys
from gui import GUI_CTRL_MODE_FLAG
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider
from messenger import MessengerEntry

import xvm_main.python.config as config
from xfw.events import registerEvent
from xvm_main.python.logger import *


MODIFIERS = {'none':  Keys.KEY_NONE,
             'shift': Keys.MODIFIER_SHIFT,
             'ctrl':  Keys.MODIFIER_CTRL,
             'alt':   Keys.MODIFIER_ALT}


@registerEvent(game, 'handleKeyEvent', True)
def game_handleKeyEvent(event):
    sessionProvider = dependency.instance(IBattleSessionProvider)
    hotkey = config.get('hotkeys/quicklyLeave', {'enabled': True, 'keyCode': Keys.KEY_F4, 'modifier': 'none'})
    if hotkey.get('enabled', True) and sessionProvider.getArenaDP() is not None:
        if MessengerEntry.g_instance.gui.isFocused():
            return
        isDown, key, mods, isRepeat = game.convertKeyEvent(event)
        if key == hotkey.get('keyCode', Keys.KEY_F4) and isDown and not isRepeat:
            modifier = str(hotkey.get('modifier', 'none')).lower()
            if mods != MODIFIERS.get(modifier, 'none'):
                return
            exitResult = sessionProvider.getExitResult()
            if exitResult.isDeserter:
                return
            # BigWorld.player().setForcedGuiControlMode(GUI_CTRL_MODE_FLAG.CURSOR_VISIBLE)
            sessionProvider.exit()
