import BigWorld, CommandMapping, traceback
from math import ceil
from xfw import registerEvent, overrideMethod
from xvm_main.python import config
from xvm_main.python.xvm import l10n
from Avatar import PlayerAvatar
from items import vehicles
from Vehicle import Vehicle
from messenger import MessengerEntry
from functools import partial
from constants import ATTACK_REASONS
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from frameworks.wulf import WindowLayer
from gui.shared.personality import ServicesLocator
from gui.Scaleform.daapi.view.battle.shared.indicators import SixthSenseIndicator
from gui.battle_control import avatar_getter
from gui.shared.gui_items.Vehicle import VEHICLE_CLASS_NAME

SEND_TIMEOUT = 0.5

battleMessagesConfig = config.get('battleMessages', {
    'enabled': False,
    'teamDamage': { 'enabled': False },
    'enemyArtyCooldown': { 'enabled': False },
    'iAmSpotted': { 'enabled': False },
    'clipCooldownTimeMsgOnReload': { 'enabled': False },
    'attackCommandOnSight': { 'enabled': False }
})

def _getL10n(text):
    if text.find('{{l10n:') > -1:
        return l10n(text)
    return text

def getSquarePosition():
    
    def clamp(val, vmax):
        vmin = 0.1
        return vmin if (val < vmin) else vmax if (val > vmax) else val
    
    def pos2name(pos):
        sqrsName = 'KJHGFEDCBA'
        linesName = '1234567890'
        return '{}{}'.format(sqrsName[int(pos[1]) - 1], linesName[int(pos[0]) - 1])
    
    player = BigWorld.player()
    boundingBox = player.arena.arenaType.boundingBox
    position = BigWorld.entities[player.playerVehicleID].position
    
    positionRect = (position[0], position[2])
    bottomLeft, upperRight = boundingBox
    spaceSize = upperRight - bottomLeft
    relPos = positionRect - bottomLeft
    relPos[0] = clamp(relPos[0], spaceSize[0])
    relPos[1] = clamp(relPos[1], spaceSize[1])
    
    return pos2name((ceil(relPos[0] / spaceSize[0] * 10), ceil(relPos[1] / spaceSize[1] * 10)))

#ENEMYARTYCOOLDOWN

def showEnemyArtyCooldown(attackerID):
    player = BigWorld.player()
    attacker = player.arena.vehicles.get(attackerID)
    if attacker is None:
        return
    if attacker['vehicleType'] is None:
        return
    if vehicles.getVehicleClass(attacker['vehicleType'].type.compactDescr) == VEHICLE_CLASS_NAME.SPG:
        if player.team != attacker['team']:
            message = _getL10n(battleMessagesConfig['enemyArtyCooldown']['format'])
            message = message.replace('{{arty-tank}}', attacker['vehicleType'].type.shortUserString)
            message = message.replace('{{arty-name}}', attacker['name'])
            player.guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(message, 0)

@registerEvent(Vehicle, 'showDamageFromShot')
def showDamageFromShot(self, attackerID, points, effectsIndex, damageFactor):
    if battleMessagesConfig['enabled'] and battleMessagesConfig['enemyArtyCooldown']['enabled']:
        if self.isPlayerVehicle and self.isAlive():
            showEnemyArtyCooldown(attackerID)

@registerEvent(Vehicle, 'showDamageFromExplosion')
def showDamageFromExplosion(self, attackerID, center, effectsIndex, damageFactor):
    if battleMessagesConfig['enabled'] and battleMessagesConfig['enemyArtyCooldown']['enabled']:
        if self.isPlayerVehicle and self.isAlive():
            showEnemyArtyCooldown(attackerID)

#IAMSPOTTED

def iAmSpotted():
    
    def sosCommand(player):
        player.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.SOS)
    
    player = BigWorld.player()
    alive_allies = {id: data for id, data in player.arena.vehicles.items() if data['team'] == player.team and data['isAlive']}
    if (2 < len(alive_allies) < int(battleMessagesConfig['iAmSpotted']['showWhenLess'])) or (int(battleMessagesConfig['iAmSpotted']['showWhenLess']) == 0):
        message = _getL10n(battleMessagesConfig['iAmSpotted']['format'])
        message = message.replace('{{position}}', getSquarePosition())
        if len(message) > 0:
            player.guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(message, 0)
        if battleMessagesConfig['iAmSpotted']['helpMeCommand']:
            BigWorld.callback(SEND_TIMEOUT, partial(sosCommand, player))

@registerEvent(SixthSenseIndicator, '_SixthSenseIndicator__show')
def _SixthSenseIndicator__show(self):
    if battleMessagesConfig['enabled'] and battleMessagesConfig['iAmSpotted']['enabled'] and BigWorld.player().isVehicleAlive:
        iAmSpotted()

#TEAMDAMAGE

def showTeamDamage(message):
    messageIn = battleMessagesConfig['teamDamage']['messageIn']
    if messageIn == 'chat':
        MessengerEntry.g_instance.gui.addClientMessage(message)
    elif messageIn == 'killog':
        ctrl = ServicesLocator.appLoader.getDefBattleApp()
        if ctrl is not None:
            battle_page = ctrl.containerManager.getContainer(WindowLayer.VIEW).getView()
            battle_page.components['battlePlayerMessages'].as_showRedMessageS(None, message)

def teamDamage_onHealthChanged(self, diffHealth, attackerID, attackReasonID):
    player = BigWorld.player()
    attacker = avatar_getter.getArena().vehicles.get(attackerID)
    if (None in (player, attacker)) or (diffHealth <= battleMessagesConfig['teamDamage']['ignoreLessThan']):
        return
    if (player.team == attacker['team'] == self.publicInfo.team) and (self.id != attackerID):
        message = _getL10n(battleMessagesConfig['teamDamage']['format'])
        message = message.replace('{{damage}}', str(diffHealth))
        message = message.replace('{{damage-reason}}', l10n(ATTACK_REASONS[attackReasonID]))
        message = message.replace('{{victim-name}}', self.publicInfo.name)
        message = message.replace('{{victim-vehicle}}', self.typeDescriptor.type.shortUserString)
        message = message.replace('{{attacker-name}}', attacker['name'])
        message = message.replace('{{attacker-vehicle}}', attacker['vehicleType'].type.shortUserString)
        
        enabledFor = battleMessagesConfig['teamDamage']['enabledFor']
        if enabledFor == 'all':
            showTeamDamage(message)
        elif (enabledFor == 'player') and ((self.publicInfo.name == player.name) or (attacker['name'] == player.name)):
            showTeamDamage(message)
        elif (enabledFor == 'ally') and (self.publicInfo.name != player.name) and (attacker['name'] != player.name):
            showTeamDamage(message)

@registerEvent(Vehicle, 'onHealthChanged')
def onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID):
    if battleMessagesConfig['enabled'] and battleMessagesConfig['teamDamage']['enabled']:
        teamDamage_onHealthChanged(self, oldHealth - newHealth, attackerID, attackReasonID)

#CLIPCOOLDOWNTIMEMSGONRELOAD

def clipCooldownTimeMsgOnReload(avatar):
    message = _getL10n(battleMessagesConfig['clipCooldownTimeMsgOnReload']['format'])
    if len(message) > 0:
        message = message.replace('{{clipReloadTime}}', '{}'.format(ceil(avatar.guiSessionProvider.shared.ammo.getGunReloadingState().getTimeLeft())))
        avatar.guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(message, 0)
    else:
        avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.RELOADINGGUN)

@overrideMethod(PlayerAvatar, 'handleKey')
def handleKey(base, self, isDown, key, mods):
    if battleMessagesConfig['enabled'] and battleMessagesConfig['clipCooldownTimeMsgOnReload']['enabled']:
        try:
            cmdMap = CommandMapping.g_instance
            if cmdMap.isFired(CommandMapping.CMD_RELOAD_PARTIAL_CLIP, key) and isDown and self.isVehicleAlive:
                self.guiSessionProvider.shared.ammo.reloadPartialClip(self)
                BigWorld.callback(SEND_TIMEOUT, partial(clipCooldownTimeMsgOnReload, self))
                return True
        except:
            traceback.print_exc()
    
    base(self, isDown, key, mods)

#ATTACKENEMYONSIGHT

lastAttackCommandTime = 0

def attackEnemyCommandOnSight(avatar, target):
    global lastAttackCommandTime
    
    if ((BigWorld.serverTime() - lastAttackCommandTime) > battleMessagesConfig['attackCommandOnSight']['timeout']) and (BigWorld.target() == target):
        avatar.guiSessionProvider.shared.chatCommands.sendTargetedCommand(BATTLE_CHAT_COMMAND_NAMES.ATTACK_ENEMY, target.id)
    
    lastAttackCommandTime = BigWorld.serverTime()

@registerEvent(PlayerAvatar, 'targetFocus')
def targetFocus(self, entity):
    if battleMessagesConfig['enabled'] and battleMessagesConfig['attackCommandOnSight']['enabled']:
        if self.isVehicleAlive and entity.isAlive() and hasattr(entity, 'publicInfo') and (self.team != entity.publicInfo['team']):
            BigWorld.callback(float(battleMessagesConfig['attackCommandOnSight']['delay']), partial(attackEnemyCommandOnSight, self, entity))
