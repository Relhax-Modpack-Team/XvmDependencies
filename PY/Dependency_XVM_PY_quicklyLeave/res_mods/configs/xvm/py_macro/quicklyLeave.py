import BigWorld
import game
import Keys
from gui import GUI_CTRL_MODE_FLAG
from gui.Scaleform.daapi.view.battle.shared.ingame_menu import _ARENAS_WITHOUT_DEZERTER_PUNISHMENTS
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider
from messenger import MessengerEntry

import xvm_main.python.config as config
from xfw.events import registerEvent
from xvm_main.python.logger import *


MODIFIERS = {'none':  0,
             'shift': 1,
             'ctrl':  2,
             'alt':   4}


@registerEvent(game, 'handleKeyEvent', True)
def game_handleKeyEvent(event):
    sessionProvider = dependency.instance(IBattleSessionProvider)
    hotkey = config.get('hotkeys/quicklyLeave', {'enabled': True, 'keyCode': Keys.KEY_F4, 'modifier': 'none'})
    if hotkey.get('enabled', True) and sessionProvider.getArenaDP() is not None:
        if MessengerEntry.g_instance.gui.isFocused():
            return
        isDown, key, mods, isRepeat = game.convertKeyEvent(event)
        if key == hotkey.get('keyCode', Keys.KEY_F4) and isDown and not isRepeat and mods == MODIFIERS.get(hotkey.get('modifier', 'none').lower()):
            exitResult = sessionProvider.getExitResult()
            arenaType = sessionProvider.arenaVisitor.getArenaGuiType()
            if exitResult.isDeserter and arenaType not in _ARENAS_WITHOUT_DEZERTER_PUNISHMENTS:
                return
            # BigWorld.player().setForcedGuiControlMode(GUI_CTRL_MODE_FLAG.CURSOR_VISIBLE)
            sessionProvider.exit()
