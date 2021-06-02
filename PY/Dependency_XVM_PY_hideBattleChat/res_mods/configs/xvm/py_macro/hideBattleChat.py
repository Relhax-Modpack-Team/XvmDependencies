import game
import Keys
from messenger.gui.Scaleform.battle_entry import BattleEntry
from messenger import MessengerEntry

import xvm_main.python.config as config
from xfw.events import registerEvent
from xvm_main.python.logger import *


@registerEvent(game, 'handleKeyEvent', True)
def game_handleKeyEvent(event):
    hotkey = config.get('hotkeys/hideBattleChat', {'enabled': True, 'keyCode': Keys.KEY_H})
    if hotkey.get('enabled', True):
        gui = MessengerEntry.g_instance.gui
        if gui.isFocused():
            return
        isDown, key, mods, isRepeat = game.convertKeyEvent(event)
        if key == hotkey.get('keyCode', Keys.KEY_H) and isDown and not isRepeat:
            entry = gui._GUIDecorator__current()
            if isinstance(entry, BattleEntry):
                view = entry._BattleEntry__view()
                if view is not None:
                    view.flashObject.visible = not view.flashObject.visible
