import game
from gui.Scaleform.daapi.view.battle.shared.ingame_menu import _ARENAS_WITHOUT_DEZERTER_PUNISHMENTS
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider
from messenger import MessengerEntry

import xvm_main.python.config as config
from xfw.events import registerEvent
from xvm_main.python.logger import *


@registerEvent(game, 'handleKeyEvent', True)
def game_handleKeyEvent(event):
    sessionProvider = dependency.instance(IBattleSessionProvider)
    hotkey = config.get('hotkeys/quicklyLeave', {'enabled': True, 'keyCode': 62})
    if hotkey.get('enabled', True) and sessionProvider.getArenaDP() is not None:
        if MessengerEntry.g_instance.gui.isFocused():
            return
        isDown, key, mods, isRepeat = game.convertKeyEvent(event)
        if key == hotkey.get('keyCode', 62) and isDown and not isRepeat:
            exitResult = sessionProvider.getExitResult()
            arenaType = sessionProvider.arenaVisitor.getArenaGuiType()
            if exitResult.isDeserter and arenaType not in _ARENAS_WITHOUT_DEZERTER_PUNISHMENTS:
                return
            sessionProvider.exit()
