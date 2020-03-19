from Avatar import PlayerAvatar
from BigWorld import cancelCallback, time, callback
from Vehicle import Vehicle
from constants import ARENA_GUI_TYPE
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import AmmoPlugin
from gui.Scaleform.daapi.view.battle.shared.damage_panel import DamagePanel
from gui.Scaleform.daapi.view.meta.CrosshairPanelContainerMeta import CrosshairPanelContainerMeta
from gui.Scaleform.daapi.view.meta.DualGunPanelMeta import DualGunPanelMeta
from gui.battle_control.controllers.consumables.ammo_ctrl import AmmoReplayPlayer
from AvatarInputHandler import AvatarInputHandler
from aih_constants import CTRL_MODE_NAME

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
from xfw.events import registerEvent, overrideMethod
from xfw_actionscript.python import *
from xvm_main.python.logger import *

leftTime = None
leftTimeShot = None
reloadTime = None
reloadTimeClip = None
endReloadTime = 0.0
endAutoReloadTime = None
endReloadTimeShot = None
isAutoReload = False
isDualGun = False
autoReloadTime = None
autoReloadTimes = []
autoReloadLeftTime = None
reloadTimesClip = []
quantityInClipShells = 0
quantityInClipShellsMax = 0
isAlive = True
reloadTimerCallbackID = None
autoReloadTimerCallbackID = None
reloadShotTimerCallbackID = None
tankmenAndDevicesReload = []
increasedReload = []
gunsState = [False, False]
isPreparingSalvo = False
isGunBlocked = False
visible = True
DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]


def resetCallback(CallbackID):
    if CallbackID is not None:
        cancelCallback(CallbackID)
    return None

def reloadTimer():
    global leftTime, reloadTimerCallbackID
    if leftTime is None:
        return
    leftTime = max(0.0, endReloadTime - time())
    if leftTime > 0.0:
        reloadTimerCallbackID = callback(0.1, reloadTimer)
    else:
        reloadTimerCallbackID = None
    if not isAutoReload:
        as_event('ON_RELOAD')


def reloading(duration, baseTime, startTime=0.0):
    global leftTime, reloadTime, endReloadTime, reloadTimeClip, reloadTimerCallbackID
    reloadTimerCallbackID = resetCallback(reloadTimerCallbackID)
    if duration > 0.0:
        leftTime = duration if leftTime != 0.0 else (duration - startTime)
        endReloadTime = time() + leftTime
        reloadTimerCallbackID = callback(0.1, reloadTimer)
    else:
        leftTime = 0.0
    if (baseTime != 0.0) and ((reloadTimeClip is None) or (abs(reloadTimeClip - baseTime) > 0.01)):
        reloadTime = baseTime
    if not isAutoReload:
        as_event('ON_RELOAD')


def autoReloadTimer():
    global autoReloadLeftTime, autoReloadTimerCallbackID, leftTime
    if autoReloadLeftTime is None:
        return
    autoReloadLeftTime = max(0.0, endAutoReloadTime - time())
    leftTime = max(0.0, endReloadTime - time())
    if (autoReloadLeftTime > 0.0) or (leftTime > 0.0):
        autoReloadTimerCallbackID = callback(0.1, autoReloadTimer)
    else:
        autoReloadTimerCallbackID = None
    as_event('ON_RELOAD')


def autoReloading(duration, baseTime):
    global autoReloadLeftTime, autoReloadTime, endAutoReloadTime, autoReloadTimerCallbackID, endReloadTime, leftTime, reloadTime
    _currentReloadTimeInClip = autoReloadTimes[quantityInClipShells]
    factor = (baseTime / _currentReloadTimeInClip) if _currentReloadTimeInClip != 0 else 0
    autoReloadTime = factor * reloadTimesClip[0]
    # log('autoReloadTime = %s, factor = %s, reloadTimesClip[0] = %s' % (autoReloadTime, factor, reloadTimesClip[0]))
    autoReloadTimerCallbackID = resetCallback(autoReloadTimerCallbackID)
    if duration > 0.0:
        autoReloadLeftTime = duration + factor * reloadTimesClip[quantityInClipShells + 1]
        leftTime = duration
        currentTime = time()
        endAutoReloadTime = currentTime + autoReloadLeftTime
        endReloadTime = currentTime + duration
        autoReloadTimerCallbackID = callback(0.1, autoReloadTimer)
    else:
        leftTime = autoReloadLeftTime = 0.0
    reloadTime = baseTime
    # log('autoReloading: [%s] autoReloadTime = %s, factor = %s, autoReloadLeftTime = %s' % (quantityInClipShells, autoReloadTime, factor, autoReloadLeftTime))
    as_event('ON_RELOAD')


def reloadShotTimer():
    global leftTimeShot, reloadShotTimerCallbackID
    if leftTimeShot is None:
        return
    leftTimeShot = max(0.0, endReloadTimeShot - time())
    if leftTimeShot > 0.0:
        reloadShotTimerCallbackID = callback(0.1, reloadShotTimer)
    else:
        reloadShotTimerCallbackID = None
    as_event('ON_RELOAD')


def reloadingShot(duration):
    global leftTimeShot, reloadShotTimerCallbackID, endReloadTimeShot
    reloadShotTimerCallbackID = resetCallback(reloadShotTimerCallbackID)
    if duration > 0.0:
        leftTimeShot = duration
        endReloadTimeShot = time() + duration
        reloadShotTimerCallbackID = callback(0.1, reloadShotTimer)
    else:
        leftTimeShot = 0.0
    as_event('ON_RELOAD')


@registerEvent(AmmoPlugin, '_AmmoPlugin__onGunReloadTimeSet')
def reloading__onGunReloadTimeSet(self, _, state):
    if config.get('sight/enabled', True) and self._AmmoPlugin__guiSettings.hasAutoReload and not isDualGun and battle.isBattleTypeSupported and isAlive:
        reloadingShot(state.getTimeLeft())
    # log('onGunReloadTimeSet    hasAutoReload = %s    leftTeme = %s    getActualValue = %s    getBaseValue = %s' % (self._AmmoPlugin__guiSettings.hasAutoReload, state.getTimeLeft(), state.getActualValue(), state.getBaseValue()))


@registerEvent(AmmoPlugin, '_AmmoPlugin__onGunAutoReloadTimeSet')
def reloading__onGunAutoReloadTimeSet(self, state, stunned):
    if config.get('sight/enabled', True) and isAutoReload and not isDualGun and battle.isBattleTypeSupported and isAlive:
        # autoReloading(state.getTimeLeft(), state.getBaseValue())
        # log('onGunAutoReloadTimeSet     leftTeme = %s   getActualValue = %s    baseTime = %s' % (state.getTimeLeft(), state.getActualValue(), state.getBaseValue()))

        autoReloading(state.getTimeLeft(), state.getBaseValue())

    # log('__onGunAutoReloadTimeSet: getBaseValue = %s, getActualValue = %s, getTimeLeft = %s' % (state.getBaseValue(), state.getActualValue(), state.getTimeLeft()))
    # log('state= %s' % (filter(lambda x: not x.startswith('_'), dir(state))))


@registerEvent(CrosshairPanelContainerMeta, 'as_setAmmoStockS')
def reloading_as_setAmmoStockS(self, quantity, quantityInClip, isLow, clipState, clipReloaded):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and not isDualGun and isAlive:
        global quantityInClipShells
        quantityInClipShells = max(quantityInClip, 0) if quantityInClipShellsMax > 1 else None


@registerEvent(CrosshairPanelContainerMeta, 'as_setReloadingS')
def reloading_as_setReloadingS(self, duration, baseTime, startTime, isReloading):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and not isDualGun and isAlive:
        # log('as_setReloadingS =    duration = %s  baseTime = %s' % (duration, baseTime))
        reloading(duration, baseTime, startTime)


@registerEvent(AmmoReplayPlayer, 'setGunAutoReloadTime')
def reloading_setGunAutoReloadTime(self, timeLeft, baseTime, isSlowed):
    if config.get('sight/enabled', True) and isAutoReload and not isDualGun and battle.isBattleTypeSupported and isAlive:
        # log('setGunAutoReloadTime =    leftTeme = %s  baseTime = %s' % (timeLeft, baseTime))
        autoReloading(timeLeft, baseTime)


@registerEvent(AmmoReplayPlayer, 'setGunReloadTime')
def reloading_setGunReloadTime(self, timeLeft, baseTime):
    if config.get('sight/enabled', True) and not isAutoReload and not isDualGun and battle.isBattleTypeSupported and isAlive:
        # log('setGunReloadTime =    leftTeme = %s  baseTime = %s' % (timeLeft, baseTime))
        reloading(timeLeft, baseTime)


@registerEvent(DamagePanel, '_updateStun')
def reloading_updateStun(self, stunInfo):
    global increasedReload
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and isAlive:
        stunDuration = stunInfo.duration
        if (stunDuration > 0) and ('stun' not in increasedReload):
            increasedReload.append('stun')
            as_event('ON_RELOAD')
        elif (stunDuration <= 0) and ('stun' in increasedReload):
            increasedReload.remove('stun')
            as_event('ON_RELOAD')
        # log('_updateStun increasedReload = %s' % increasedReload)


@registerEvent(DamagePanel, '_updateDeviceState')
def reloading_updateDeviceState(self, value):
    global increasedReload
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and isAlive:
        role = value[0][:-1] if value[0] in ('gunner1', 'gunner2', 'radioman1', 'radioman2', 'loader1', 'loader2') else value[0]
        if role in tankmenAndDevicesReload:
            if value[1] == 'normal' and role in increasedReload:
                increasedReload.remove(role)
                as_event('ON_RELOAD')
            elif value[1] in ['critical', 'destroyed']:
                increasedReload.append(role)
                as_event('ON_RELOAD')
        # log('_updateDeviceState increasedReload = %s' % increasedReload)
        # log('_updateDeviceState role = %s    state = %s' % (value[0], value[1]))


@registerEvent(DualGunPanelMeta, 'as_updateTotalTimeS')
def as_updateTotalTimeS(self, value):
    global autoReloadTime
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and isAlive:
        value = round(value / 1000.0, 2)
        if autoReloadTime != value:
            autoReloadTime = value
            as_event('ON_RELOAD')


@registerEvent(DualGunPanelMeta, 'as_setGunStateS')
def as_setGunStateS(self, gunId, state, timeLeft, totalTime):
    global reloadTime, reloadShotTimerCallbackID, leftTimeShot
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and isAlive:
        if reloadTime is None:
            reloadTime = round(totalTime / 1000.0, 2)
        if state == 2:
            reloadShotTimerCallbackID = resetCallback(reloadShotTimerCallbackID)
            leftTimeShot = 0.0
            reloading(round(timeLeft / 1000.0, 2), round(totalTime / 1000.0, 2))
        gunsState[gunId] = (state == 3)


@registerEvent(DualGunPanelMeta, 'as_updateActiveGunS')
def as_updateActiveGunS(self, activeGunId, timeLeft, totalTime):
    global isGunBlocked
    if (gunsState[0] + gunsState[1]) == 1:
        if timeLeft > 0:
            isGunBlocked = True
            reloadingShot(round(timeLeft / 1000.0, 2))
        elif isGunBlocked:
            isGunBlocked = False
            as_event('ON_RELOAD')


@registerEvent(DualGunPanelMeta, 'as_startChargingS')
def as_startChargingS(self, timeLeft, totalTime):
    global isPreparingSalvo
    if timeLeft > 0 and (gunsState[0] + gunsState[1]) == 2:
        isPreparingSalvo = True
        reloadingShot(round(timeLeft / 1000.0, 2))


@registerEvent(DualGunPanelMeta, 'as_cancelChargeS')
def as_cancelChargeS(self):
    global reloadShotTimerCallbackID, isPreparingSalvo, leftTimeShot
    isPreparingSalvo = False
    leftTimeShot = 0.0
    reloadShotTimerCallbackID = resetCallback(reloadShotTimerCallbackID)
    as_event('ON_RELOAD')


@registerEvent(DualGunPanelMeta, 'as_setCooldownS')
def as_setCooldownS(self, timeLeft):
    global isPreparingSalvo
    if timeLeft > 0 and (gunsState[0] + gunsState[1]) == 0:
        isPreparingSalvo = False
        reloadingShot(round(timeLeft / 1000.0 - reloadTime, 2))


@registerEvent(Vehicle, 'onEnterWorld')
def reloading_onEnterWorld(self, prereqs):
    global leftTime, reloadTime, endReloadTime, reloadTimeClip, isAutoReload, autoReloadTimes, increasedReload, gunsState, visible
    global quantityInClipShellsMax, quantityInClipShells, autoReloadLeftTime, autoReloadTime, tankmenAndDevicesReload, isDualGun, isGunBlocked
    global isAlive, reloadTimesClip, reloadTimerCallbackID, autoReloadTimerCallbackID, leftTimeShot, reloadShotTimerCallbackID, isPreparingSalvo
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        isAlive = True
        leftTime = None
        leftTimeShot = None
        reloadTime = None
        autoReloadLeftTime = None
        autoReloadTime = None
        endReloadTime = 0.0
        gunsState = [False, False]
        isPreparingSalvo = False
        isGunBlocked = False
        gun = self.typeDescriptor.gun
        tankmenAndDevicesReload = [role[0] for role in self.typeDescriptor.type.crewRoles if 'loader' in role]
        tankmenAndDevicesReload.append('ammoBay')
        increasedReload = []
        # log('tankmenAndDevicesReload = %s' % tankmenAndDevicesReload)
        # for i, v in enumerate(self.typeDescriptor.type.crewRoles):
        #     log('typeDescriptor.type.crewRoles[%s] = %s' % (i, v))

        quantityInClipShells = 0
        quantityInClipShellsMax = 2 if isDualGun else gun.clip[0]
        isAutoReload = (gun.autoreload.reloadTime[0] != 0.0)
        isDualGun = self.typeDescriptor.isDualgunVehicle
        if isAutoReload:
            autoReloadTimes = list(gun.autoreload.reloadTime)
            reloadTimesClip = []
            prev = 0
            for t in autoReloadTimes:
                reloadTimesClip.append(t + prev)
                prev += t
            reloadTimesClip.reverse()
            reloadTimesClip.append(0.0)
            reloadTimesClip.append(0.0)
            autoReloadTimes.reverse()
            autoReloadTimes.append(autoReloadTimes[len(autoReloadTimes) - 1])
        else:
            autoReloadTimes = None
        reloadTimerCallbackID = resetCallback(reloadTimerCallbackID)
        autoReloadTimerCallbackID = resetCallback(autoReloadTimerCallbackID)
        reloadShotTimerCallbackID = resetCallback(reloadShotTimerCallbackID)
        reloadTimeClip = gun.clip[1] if gun.clip[0] > 1 else None
        visible = True
        as_event('ON_RELOAD')


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    newVisible = eMode in DISPLAY_IN_MODES
    if newVisible != visible:
        visible = newVisible
        as_event('ON_RELOAD')


@registerEvent(PlayerAvatar, 'updateVehicleHealth')
def PlayerAvatar_updateVehicleHealth(self, vehicleID, health, deathReasonID, isCrewActive, isRespawn):
    global leftTime, reloadTime, endReloadTime, reloadTimeClip, autoReloadLeftTime, autoReloadTime, isAlive, leftTimeShot, isGunBlocked
    global increasedReload, reloadTimerCallbackID, autoReloadTimerCallbackID, reloadShotTimerCallbackID, isPreparingSalvo
    if not (health > 0 and isCrewActive) and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        isAlive = False
        leftTime = None
        leftTimeShot = None
        reloadTime = None
        reloadTimeClip = None
        endReloadTime = 0.0
        autoReloadLeftTime = None
        autoReloadTime = None
        increasedReload = []
        isPreparingSalvo = False
        isGunBlocked = False
        reloadTimerCallbackID = resetCallback(reloadTimerCallbackID)
        autoReloadTimerCallbackID = resetCallback(autoReloadTimerCallbackID)
        reloadShotTimerCallbackID = resetCallback(reloadShotTimerCallbackID)
        as_event('ON_RELOAD')


@xvm.export('sight.leftTime', deterministic=False)
def sight_leftTime(norm=None):
    if not visible:
        return None
    if norm is None:
        return leftTime
    elif reloadTime is not None:
        return 0 if reloadTime == 0.0 else int((reloadTime - leftTime) * norm // reloadTime)
    else:
        return None


@xvm.export('sight.reloadPercent', deterministic=False)
def sight_reloadPercent():
    if reloadTime is not None and leftTime is not None and visible:
        return 0 if reloadTime == 0 else int((reloadTime - leftTime) * 100 // reloadTime)
    return None


@xvm.export('sight.reloadTime', deterministic=False)
def sight_reloadTime():
    return reloadTime if visible else None


@xvm.export('sight.reloadTimeClip', deterministic=False)
def sight_reloadTimeClip():
    return reloadTimeClip if visible else None


@xvm.export('sight.aLeftTime', deterministic=False)
def sight_aleftTime(norm=None):
    if not visible:
        return None
    if isDualGun and reloadTime is not None and leftTime is not None:
        _leftTime = leftTime if (gunsState[0] + gunsState[1]) > 0 else leftTime + reloadTime
        if norm is None:
            return _leftTime
        elif autoReloadTime is not None:
            return 0 if autoReloadTime == 0.0 else int((autoReloadTime - _leftTime) * norm // autoReloadTime)
    elif autoReloadTime is not None:
        if norm is None:
            return autoReloadLeftTime
        else:
            return 0 if autoReloadTime == 0.0 else int((autoReloadTime - autoReloadLeftTime) * norm // autoReloadTime)
    return None


@xvm.export('sight.leftTimeShot', deterministic=False)
def sight_leftTimeShot():
    if not isAlive or not visible:
        return None
    if isDualGun:
        numberLoadedGuns = gunsState[0] + gunsState[1]
        if numberLoadedGuns == 0:
            return leftTime if leftTime > 0.0 else leftTimeShot
        elif numberLoadedGuns == 1 or numberLoadedGuns == 2:
            return leftTimeShot
        else:
            return 0.0
    return leftTimeShot


@xvm.export('sight.aReloadTime', deterministic=False)
def sight_aReloadTime():
    return autoReloadTime if visible else None


@xvm.export('sight.isIncreasedReload', deterministic=False)
def sight_isIncreasedReload():
    return '#FF0000' if increasedReload else None


@xvm.export('sight.isPreparingSalvo', deterministic=False)
def sight_preparingSalvo():
    return 'prepare' if isPreparingSalvo and visible else None


@xvm.export('sight.isGunBlocked', deterministic=False)
def sight_isGunBlocked():
    return 'blocked' if isGunBlocked and visible else None
