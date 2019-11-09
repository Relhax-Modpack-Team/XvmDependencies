from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.Scaleform.daapi.view.meta.CrosshairPanelContainerMeta import CrosshairPanelContainerMeta

from xfw import *
from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle


quantityShells = None
quantityInClipShells = None
quantityInClipShellsMax = None
burst = None
playerVehicleID = None


@registerEvent(CrosshairPanelContainerMeta, 'as_setAmmoStockS')
def CrosshairPanelContainerMeta_as_setAmmoStockS(self, quantity, quantityInClip, isLow, clipState, clipReloaded):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global quantityShells, quantityInClipShells
        quantityShells = max(quantity, 0)
        quantityInClipShells = max(quantityInClip, 0) if quantityInClipShellsMax > 1 else None
        as_event('ON_AMMO_COUNT')


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global quantityShells, quantityInClipShells, burst, quantityInClipShellsMax, playerVehicleID
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        quantityShells = None
        quantityInClipShells = None
        gun = self.typeDescriptor.gun
        quantityInClipShellsMax = gun.clip[0]
        burst = gun.burst[0]
        playerVehicleID = self.id
        as_event('ON_AMMO_COUNT')


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    global quantityShells, quantityInClipShells, burst, quantityInClipShellsMax
    if (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID) and battle.isBattleTypeSupported:
        quantityShells = None
        quantityInClipShells = None
        quantityInClipShellsMax = None
        burst = None
        as_event('ON_AMMO_COUNT')


@xvm.export('sight.quantityShells', deterministic=False)
def sight_quantityShells():
    return quantityShells


@xvm.export('sight.quantityInClipShells', deterministic=False)
def sight_quantityInClipShells():
    return quantityInClipShells


@xvm.export('sight.quantityInClipShellsMax', deterministic=False)
def sight_quantityInClipShellsMax():
    return quantityInClipShellsMax


@xvm.export('sight.isFullClipShells', deterministic=False)
def sight_isFullClipShells():
    return 'full' if quantityInClipShellsMax is not None and quantityInClipShellsMax is not None and (quantityInClipShellsMax == quantityInClipShells) else None


@xvm.export('sight.burst', deterministic=False)
def sight_burst():
    return burst
