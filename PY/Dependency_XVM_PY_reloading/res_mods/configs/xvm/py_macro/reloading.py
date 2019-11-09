import BigWorld
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.battle_control.controllers.consumables.ammo_ctrl import AmmoReplayPlayer
from gui.Scaleform.daapi.view.meta.CrosshairPanelContainerMeta import CrosshairPanelContainerMeta
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import AmmoPlugin
from constants import ARENA_GUI_TYPE
from gui.Scaleform.daapi.view.battle.shared.damage_panel import DamagePanel


from xfw import *
from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle


leftTime = None
leftTimeShot = None
reloadTime = None
reloadTimeClip = None
endReloadTime = 0.0
endAutoReloadTime = None
endReloadTimeShot = None
playerVehicleID = None
isAutoReload = False
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


def reloadTimer():
    global leftTime, reloadTimerCallbackID
    if leftTime is None:
        return
    leftTime = max(0.0, endReloadTime - BigWorld.time())
    reloadTimerCallbackID = BigWorld.callback(0.1, reloadTimer) if leftTime > 0.0 else None
    if not isAutoReload:
        as_event('ON_RELOAD')


def reloading(duration, baseTime, startTime=0.0):
    global leftTime, reloadTime, endReloadTime, reloadTimeClip, reloadTimerCallbackID
    if reloadTimerCallbackID is not None:
        BigWorld.cancelCallback(reloadTimerCallbackID)
        reloadTimerCallbackID = None
    if duration > 0.0:
        leftTime = duration if leftTime != 0.0 else (duration - startTime)
        endReloadTime = BigWorld.time() + leftTime
        reloadTimerCallbackID = BigWorld.callback(0.1, reloadTimer)
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
    autoReloadLeftTime = max(0.0, endAutoReloadTime - BigWorld.time())
    leftTime = max(0.0, endReloadTime - BigWorld.time())
    autoReloadTimerCallbackID = BigWorld.callback(0.1, autoReloadTimer) if (autoReloadLeftTime > 0.0) or (leftTime > 0.0) else None
    as_event('ON_RELOAD')


def autoReloading(duration, baseTime):
    global autoReloadLeftTime, autoReloadTime, endAutoReloadTime, autoReloadTimerCallbackID, endReloadTime, leftTime, reloadTime
    _currentReloadTimeInClip = autoReloadTimes[quantityInClipShells]
    factor = (baseTime / _currentReloadTimeInClip) if _currentReloadTimeInClip != 0 else 0
    autoReloadTime = factor * reloadTimesClip[0]
    # log('autoReloadTime = %s, factor = %s, reloadTimesClip[0] = %s' % (autoReloadTime, factor, reloadTimesClip[0]))
    if autoReloadTimerCallbackID is not None:
        BigWorld.cancelCallback(autoReloadTimerCallbackID)
        autoReloadTimerCallbackID = None
    if duration > 0.0:
        autoReloadLeftTime = duration + factor * reloadTimesClip[quantityInClipShells + 1]
        leftTime = duration
        endAutoReloadTime = BigWorld.time() + autoReloadLeftTime
        endReloadTime = BigWorld.time() + duration
        autoReloadTimerCallbackID = BigWorld.callback(0.1, autoReloadTimer)
    else:
        leftTime = autoReloadLeftTime = 0.0
    reloadTime = baseTime
    # log('autoReloading: [%s] autoReloadTime = %s, factor = %s, autoReloadLeftTime = %s' % (quantityInClipShells, autoReloadTime, factor, autoReloadLeftTime))
    as_event('ON_RELOAD')

def reloadShotTimer():
    global leftTimeShot, reloadShotTimerCallbackID
    if leftTimeShot is None:
        return
    leftTimeShot = max(0.0, endReloadTimeShot - BigWorld.time())
    reloadShotTimerCallbackID = BigWorld.callback(0.1, reloadShotTimer) if leftTime > 0.0 else None
    as_event('ON_RELOAD')


def reloadingShot(duration):
    global leftTimeShot, reloadShotTimerCallbackID, endReloadTimeShot
    if reloadShotTimerCallbackID is not None:
        BigWorld.cancelCallback(reloadShotTimerCallbackID)
        reloadShotTimerCallbackID = None
    if duration > 0.0:
        leftTimeShot = duration
        endReloadTimeShot = BigWorld.time() + duration
        reloadShotTimerCallbackID = BigWorld.callback(0.1, reloadShotTimer)
    else:
        leftTimeShot = 0.0
    as_event('ON_RELOAD')


@registerEvent(AmmoPlugin, '_AmmoPlugin__onGunReloadTimeSet')
def __onGunReloadTimeSet(self, _, state):
    if config.get('sight/enabled', True) and self._AmmoPlugin__guiSettings.hasAutoReload and battle.isBattleTypeSupported and isAlive:
        reloadingShot(state.getTimeLeft())
    # log('onGunReloadTimeSet    hasAutoReload = %s    leftTeme = %s    getActualValue = %s    getBaseValue = %s' % (self._AmmoPlugin__guiSettings.hasAutoReload, state.getTimeLeft(), state.getActualValue(), state.getBaseValue()))


@registerEvent(AmmoPlugin, '_AmmoPlugin__onGunAutoReloadTimeSet')
def _AmmoPlugin__onGunAutoReloadTimeSet(self, state, stunned):
    if config.get('sight/enabled', True) and isAutoReload and battle.isBattleTypeSupported and isAlive:
        # autoReloading(state.getTimeLeft(), state.getBaseValue())
        # log('onGunAutoReloadTimeSet     leftTeme = %s   getActualValue = %s    baseTime = %s' % (state.getTimeLeft(), state.getActualValue(), state.getBaseValue()))

        autoReloading(state.getTimeLeft(), state.getBaseValue())


    # log('__onGunAutoReloadTimeSet: getBaseValue = %s, getActualValue = %s, getTimeLeft = %s' % (state.getBaseValue(), state.getActualValue(), state.getTimeLeft()))
    # log('state= %s' % (filter(lambda x: not x.startswith('_'), dir(state))))


@registerEvent(CrosshairPanelContainerMeta, 'as_setAmmoStockS')
def CrosshairPanelContainerMeta_as_setAmmoStockS(self, quantity, quantityInClip, isLow, clipState, clipReloaded):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and isAlive:
        global quantityInClipShells
        quantityInClipShells = max(quantityInClip, 0) if quantityInClipShellsMax > 1 else None


@registerEvent(AmmoReplayPlayer, 'setGunAutoReloadTime')
def setGunAutoReloadTime(self, timeLeft, baseTime, isSlowed):
    if config.get('sight/enabled', True) and isAutoReload and battle.isBattleTypeSupported and isAlive:
        # log('setGunAutoReloadTime =    leftTeme = %s  baseTime = %s' % (timeLeft, baseTime))
        autoReloading(timeLeft, baseTime)


@registerEvent(AmmoReplayPlayer, 'setGunReloadTime')
def AmmoReplayPlayer_setGunReloadTime(self, timeLeft, baseTime):
    if config.get('sight/enabled', True) and not isAutoReload and battle.isBattleTypeSupported and isAlive:
        # log('setGunReloadTime =    leftTeme = %s  baseTime = %s' % (timeLeft, baseTime))
        reloading(timeLeft, baseTime)


# @registerEvent(CrosshairPanelContainerMeta, 'as_autoloaderUpdateS')
# def as_autoloaderUpdateS(self, timeLeft, baseTime, isPause=False, isStun=False, isTimerOn=False):
#     if config.get('sight/enabled', True) and isAutoReload and not isEpicBattle:
#         log('as_autoloaderUpdateS =    leftTeme = %s  baseTime = %s' % (timeLeft, baseTime))
#         autoReloading(timeLeft, baseTime)


# @registerEvent(CrosshairPanelContainerMeta, 'as_setAutoloaderReloadingS')
# def as_setAutoloaderReloadingS(self, duration, baseTime):
#     if config.get('sight/enabled', True) and isAutoReload and not isEpicBattle:
#         log('as_setAutoloaderReloadingS =    duration = %s  baseTime = %s' % (duration, baseTime))
#         autoReloading(duration, baseTime)


@registerEvent(CrosshairPanelContainerMeta, 'as_setReloadingS')
def CrosshairPanelContainerMeta_as_setReloadingS(self, duration, baseTime, startTime, isReloading):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and isAlive:
        # log('as_setReloadingS =    duration = %s  baseTime = %s' % (duration, baseTime))
        reloading(duration, baseTime, startTime)


@registerEvent(DamagePanel, '_updateStun')
def _updateStun(self, stunInfo):
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
def _updateDeviceState(self, value):
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


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global leftTime, reloadTime, endReloadTime, reloadTimeClip, playerVehicleID, isAutoReload, autoReloadTimes, increasedReload
    global quantityInClipShellsMax, quantityInClipShells, autoReloadLeftTime, autoReloadTime, tankmenAndDevicesReload
    global isAlive, reloadTimesClip, reloadTimerCallbackID, autoReloadTimerCallbackID, leftTimeShot, reloadShotTimerCallbackID
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        isAlive = True
        leftTime = None
        leftTimeShot = None
        reloadTime = None
        autoReloadLeftTime = None
        autoReloadTime = None
        endReloadTime = 0.0
        gun = self.typeDescriptor.gun

        tankmenAndDevicesReload = [role[0] for role in self.typeDescriptor.type.crewRoles if 'loader' in role]
        tankmenAndDevicesReload.append('ammoBay')
        increasedReload = []
        # log('tankmenAndDevicesReload = %s' % tankmenAndDevicesReload)
        # for i, v in enumerate(self.typeDescriptor.type.crewRoles):
        #     log('typeDescriptor.type.crewRoles[%s] = %s' % (i, v))

        quantityInClipShells = 0
        quantityInClipShellsMax = gun.clip[0]
        isAutoReload = (gun.autoreload.reloadTime[0] != 0.0)
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
        reloadTimerCallbackID = None
        autoReloadTimerCallbackID = None
        reloadShotTimerCallbackID = None
        reloadTimeClip = gun.clip[1] if gun.clip[0] > 1 else None
        playerVehicleID = self.id
        as_event('ON_RELOAD')


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    global leftTime, reloadTime, endReloadTime, reloadTimeClip, autoReloadLeftTime, autoReloadTime, isAlive, leftTimeShot
    global increasedReload
    if (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID) and battle.isBattleTypeSupported:
        isAlive = False
        leftTime = None
        leftTimeShot =None
        reloadTime = None
        reloadTimeClip = None
        endReloadTime = 0.0
        autoReloadLeftTime = None
        autoReloadTime = None
        increasedReload = []
        as_event('ON_RELOAD')


@xvm.export('sight.leftTime', deterministic=False)
def sight_leftTime(norm=None):
    if norm is None:
        return leftTime
    elif reloadTime is not None:
        return 0 if reloadTime == 0.0 else int((reloadTime - leftTime) * norm // reloadTime)
    else:
        return None


@xvm.export('sight.reloadPercent', deterministic=False)
def sight_reloadPercent():
    if reloadTime is not None:
        return 0 if reloadTime == 0 else int((reloadTime - leftTime) * 100 // reloadTime)
    return None


@xvm.export('sight.reloadTime', deterministic=False)
def sight_reloadTime():
    return reloadTime


@xvm.export('sight.reloadTimeClip', deterministic=False)
def sight_reloadTimeClip():
    return reloadTimeClip


@xvm.export('sight.isAutoReload', deterministic=False)
def sight_isAutoReload():
    return 'auto' if isAutoReload else None


@xvm.export('sight.aLeftTime', deterministic=False)
def sight_aleftTime(norm=None):
    if autoReloadTime is not None:
        if norm is None:
            return autoReloadLeftTime
        else:
            return 0 if autoReloadTime == 0.0 else int((autoReloadTime - autoReloadLeftTime) * norm // autoReloadTime)
    return None


@xvm.export('sight.leftTimeShot', deterministic=False)
def sight_leftTimeShot():
    return leftTimeShot


@xvm.export('sight.aReloadTime', deterministic=False)
def sight_aReloadTime():
    return autoReloadTime


@xvm.export('sight.isIncreasedReload', deterministic=False)
def sight_isIncreasedReload():
    return '#FF0000' if increasedReload else None
