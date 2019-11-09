import game
from BigWorld import player, target, serverTime
from xfw import registerEvent, overrideMethod
from xvm_main.python import config
from xvm_main.python.xvm import l10n
from Avatar import PlayerAvatar
from messenger import MessengerEntry
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from xvm_main.python.logger import *

safeShotConfig = config.get('safeShot', {'enabled': False})
safeShotEnabled = safeShotConfig['enabled']
deadBlockEnabled = safeShotConfig.get('deadShotBlock', False)
deadBlockTimeOut = safeShotConfig.get('deadShotBlockTimeOut', 2)
lastClientMessageTime = None
lastChatMessageTime = None
hotKeyPressed = False
isEventBattle = False
deadDict = {}

def _getL10n(text):
    if text.find('{{l10n:') > -1:
        return l10n(text)
    return text

def addClientMessage(msg, timeout):
    global lastClientMessageTime
    if len(msg) == 0:
        return
    msg = _getL10n(msg)
    if (lastClientMessageTime is None) or (timeout == 0):
        MessengerEntry.g_instance.gui.addClientMessage(msg)
    elif (serverTime() - lastClientMessageTime) > timeout:
        MessengerEntry.g_instance.gui.addClientMessage(msg)
    lastClientMessageTime = serverTime()

def addChatMessage(msg):
    global lastChatMessageTime
    if len(msg) == 0:
        return
    msg = _getL10n(msg)
    if lastChatMessageTime is None:
        player().guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(msg, 0)
    elif (serverTime() - lastChatMessageTime) > 2:
        player().guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(msg, 0)
    lastChatMessageTime = serverTime()


###

@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    global deadDict
    if not vInfoVO.isAlive() and safeShotEnabled and deadBlockEnabled:
        deadDict.update({vInfoVO.vehicleID: serverTime()})

@registerEvent(game, 'handleKeyEvent')
def handleKeyEvent(event):
    global hotKeyPressed
    
    def changeSafeShotState():
        global safeShotEnabled
        safeShotEnabled = not safeShotEnabled
        if safeShotConfig['triggerMessage']:
            addClientMessage(safeShotConfig['triggerText']['enabled' if safeShotEnabled else 'disabled'], 0)
    
    if not (safeShotConfig['enabled'] and not isEventBattle and (safeShotConfig['disableKey'] == event.key) and not event.isRepeatedEvent() and not MessengerEntry.g_instance.gui.isFocused()):
        return
    elif safeShotConfig['onHold']:
        if not hotKeyPressed and event.isKeyDown():
            hotKeyPressed = True
            changeSafeShotState()
        elif hotKeyPressed and event.isKeyUp():
            hotKeyPressed = False
            changeSafeShotState()
    elif event.isKeyDown():
        changeSafeShotState()
    else:
        return

@overrideMethod(PlayerAvatar, 'shoot')
def shoot(base, self, isRepeat = False):
    if not (safeShotConfig['enabled'] and safeShotEnabled and not isEventBattle):
        return base(self, isRepeat)
    if target() is None:
        if safeShotConfig['wasteShotBlock']:
            addClientMessage(safeShotConfig['clientMessages']['wasteShotBlockedMessage'], 2)
            return
    elif hasattr(target().publicInfo, 'team'):
        if safeShotConfig['teamShotBlock'] and (player().team is target().publicInfo.team) and target().isAlive():
            if not (safeShotConfig['teamKillerShotUnblock'] and player().guiSessionProvider.getArenaDP().isTeamKiller(target().id)):
                addChatMessage(safeShotConfig['chatMessages']['teamShotBlockedMessage'].replace('{{target-name}}', target().publicInfo.name).replace('{{target-vehicle}}', target().typeDescriptor.type.shortUserString))
                addClientMessage(safeShotConfig['clientMessages']['teamShotBlockedMessage'], 2)
                return
        elif deadBlockEnabled and (not target().isAlive()) and ((deadBlockTimeOut == 0) or ((serverTime() - deadDict.get(target().id, 0)) < deadBlockTimeOut)):
            addClientMessage(safeShotConfig['clientMessages']['deadShotBlockedMessage'], 2)
            return
    return base(self, isRepeat)

@registerEvent(PlayerAvatar, 'onBecomePlayer')
def onBecomePlayer(self):
    global isEventBattle
    isEventBattle = player().guiSessionProvider.arenaVisitor.gui.isEventBattle()

@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def __destroyGUI(self):
    global safeShotConfig, safeShotEnabled, deadBlockEnabled, deadBlockTimeOut, lastClientMessageTime, lastChatMessageTime, hotKeyPressed, isEventBattle, deadDict
    safeShotConfig = config.get('safeShot', {'enabled': False})
    safeShotEnabled = safeShotConfig['enabled']
    deadBlockEnabled = safeShotConfig.get('deadShotBlock', False)
    deadBlockTimeOut = safeShotConfig.get('deadShotBlockTimeOut', 2)
    lastClientMessageTime = None
    lastChatMessageTime = None
    hotKeyPressed = False
    isEventBattle = False
    deadDict = {}
