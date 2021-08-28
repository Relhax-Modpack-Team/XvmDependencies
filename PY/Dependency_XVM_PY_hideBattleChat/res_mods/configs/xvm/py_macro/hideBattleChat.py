import Keys
import game
from messenger import MessengerEntry
from messenger import g_settings
from messenger.gui.Scaleform.battle_entry import BattleEntry
from messenger.gui.Scaleform.channels.layout import BattleLayout

import xvm_main.python.config as config
from xfw.events import registerEvent, overrideMethod
from xvm_main.python.logger import *


MODIFIERS = {'none':  Keys.KEY_NONE,
             'shift': Keys.MODIFIER_SHIFT,
             'ctrl':  Keys.MODIFIER_CTRL,
             'alt':   Keys.MODIFIER_ALT}

isChatDisabled = False
isChatHide = False


@registerEvent(game, 'handleKeyEvent', True)
def game_handleKeyEvent(event):
    global isChatDisabled, isChatHide
    hotkeyHide = config.get('hotkeys/hideBattleChat', {'enabled': True, 'keyCode': Keys.KEY_H, 'modifier': 'none'})
    gui = MessengerEntry.g_instance.gui
    if gui.isFocused():
        return
    if hotkeyHide.get('enabled', True):
        isDown, key, mods, isRepeat = game.convertKeyEvent(event)
        if key == hotkeyHide.get('keyCode', Keys.KEY_H) and isDown and not isRepeat:
            modifier = str(hotkeyHide.get('modifier', 'none')).lower()
            if mods != MODIFIERS.get(modifier, 'none'):
                return
            entry = gui._GUIDecorator__current()
            if isinstance(entry, BattleEntry):
                view = entry._BattleEntry__view()
                if view is not None:
                    isChatHide = not isChatHide
                    view.flashObject.visible = not isChatHide


    hotkeyDisable = config.get('hotkeys/disableBattleChat', {'enabled': True, 'keyCode': Keys.KEY_O, 'modifier': 'none'})
    if hotkeyDisable.get('enabled', True):
        isDown, key, mods, isRepeat = game.convertKeyEvent(event)
        if key == hotkeyDisable.get('keyCode', Keys.KEY_O) and isDown and not isRepeat:
            modifier = str(hotkeyDisable.get('modifier', 'none')).lower()
            if mods != MODIFIERS.get(modifier, 'none'):
                return
            entry = gui._GUIDecorator__current()
            if isinstance(entry, BattleEntry):
                view = entry._BattleEntry__view()
                if view is not None:
                    isChatDisabled = not isChatDisabled
                    g_settings.userPrefs._replace(disableBattleChat=isChatDisabled)
                    view.invalidateReceivers()



@overrideMethod(BattleLayout, 'isEnabled')
def isEnabled(base, self):
    if isChatDisabled:
        return False
    else:
        return base(self)
