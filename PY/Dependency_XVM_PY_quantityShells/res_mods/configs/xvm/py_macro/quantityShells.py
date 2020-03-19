from Avatar import PlayerAvatar
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.Scaleform.daapi.view.meta.CrosshairPanelContainerMeta import CrosshairPanelContainerMeta
from gui.Scaleform.daapi.view.battle.shared.vehicles.dualgun_component import DualGunComponent
from AvatarInputHandler import AvatarInputHandler
from aih_constants import CTRL_MODE_NAME

from xfw.events import registerEvent, overrideMethod
from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle


quantityShells = None
quantityInClipShells = None
quantityInClipShellsMax = None
burst = None
playerVehicleID = None
isAlive = True
dualGunState = [False, False]
isDualgunVehicle = False
visible = True
DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    newVisible = eMode in DISPLAY_IN_MODES
    if newVisible != visible:
        visible = newVisible
        as_event('ON_AMMO_COUNT')


@registerEvent(DualGunComponent, '_DualGunComponent__updateGunState')
def DualGunComponent__updateGunState(self, gunID, state, serverCooldownData):
    global dualGunState, quantityInClipShells
    dualGunState[gunID] = (state == 3)
    quantityInClipShells = dualGunState[0] + dualGunState[1]
    as_event('ON_AMMO_COUNT')


@registerEvent(CrosshairPanelContainerMeta, 'as_setAmmoStockS')
def CrosshairPanelContainerMeta_as_setAmmoStockS(self, quantity, quantityInClip, isLow, clipState, clipReloaded):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported and isAlive:
        global quantityShells, quantityInClipShells
        quantityShells = max(quantity, 0)
        quantityInClipShells = max(quantityInClip, 0) if quantityInClipShellsMax > 1 else None
        as_event('ON_AMMO_COUNT')


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global quantityShells, quantityInClipShells, burst, quantityInClipShellsMax, playerVehicleID, isAlive, isDualgunVehicle, dualGunState, visible
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        isAlive = self.isAlive()
        quantityShells = None
        quantityInClipShells = None
        dualGunState = [False, False]
        isDualgunVehicle = self.typeDescriptor.isDualgunVehicle
        visible = True
        if isAlive:
            if isDualgunVehicle:
                quantityInClipShellsMax = 2
                burst = 1
            else:
                gun = self.typeDescriptor.gun
                quantityInClipShellsMax = gun.clip[0]
                burst = gun.burst[0]
            playerVehicleID = self.id
        else:
            quantityInClipShellsMax = None
            burst = None
        as_event('ON_AMMO_COUNT')


@registerEvent(PlayerAvatar, 'updateVehicleHealth')
def PlayerAvatar_updateVehicleHealth(self, vehicleID, health, deathReasonID, isCrewActive, isRespawn):
    if not (health > 0 and isCrewActive) and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global quantityShells, quantityInClipShells, burst, quantityInClipShellsMax, isAlive
        isAlive = False
        quantityShells = None
        quantityInClipShells = None
        quantityInClipShellsMax = None
        burst = None
        as_event('ON_AMMO_COUNT')

# @registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
# def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
#     global quantityShells, quantityInClipShells, burst, quantityInClipShellsMax, isAlive
#     if (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID) and battle.isBattleTypeSupported:
#         isAlive = False
#         quantityShells = None
#         quantityInClipShells = None
#         quantityInClipShellsMax = None
#         burst = None
#         as_event('ON_AMMO_COUNT')


@xvm.export('sight.quantityShells', deterministic=False)
def sight_quantityShells():
    return quantityShells if visible else None


@xvm.export('sight.quantityInClipShells', deterministic=False)
def sight_quantityInClipShells():
    return quantityInClipShells if visible else None


@xvm.export('sight.quantityInClipShellsMax', deterministic=False)
def sight_quantityInClipShellsMax():
    return quantityInClipShellsMax if visible else None


@xvm.export('sight.isFullClipShells', deterministic=False)
def sight_isFullClipShells():
    result = (dualGunState[0] and dualGunState[1]) if isDualgunVehicle else (quantityInClipShellsMax is not None and (quantityInClipShellsMax == quantityInClipShells))
    return 'full' if result and visible else None


@xvm.export('sight.burst', deterministic=False)
def sight_burst():
    return burst if visible else None

