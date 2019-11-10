import BigWorld
import gui.Scaleform.daapi.view.battle.shared.crosshair.plugins as plug
from Avatar import PlayerAvatar
from Math import Vector3
from Vehicle import Vehicle
from VehicleGunRotator import VehicleGunRotator
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.Scaleform.daapi.view.meta.CrosshairPanelContainerMeta import CrosshairPanelContainerMeta
from gui.battle_control.controllers.consumables.ammo_ctrl import AmmoReplayPlayer

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
from xfw import *
from xvm_main.python.logger import *


vehicle = None
sphere = None
_explosionRadius = None
isDisplaySphere = False
isDownHotkey = True

VEHICLE_CLASSES = {'mediumTank': 'MT', 'lightTank': 'LT', 'heavyTank': 'HT', 'AT-SPG': 'TD', 'SPG': 'SPG'}


def explosionRadius():
    global _explosionRadius
    if vehicle is None or not hasattr(vehicle, 'typeDescriptor'):
        return
    _type = vehicle.typeDescriptor.shot.shell.type
    _explosionRadius = _type.explosionRadius if hasattr(_type, 'explosionRadius') else None


@registerEvent(plug.AmmoPlugin, '_AmmoPlugin__onGunAutoReloadTimeSet')
def _AmmoPlugin__onGunAutoReloadTimeSet(self, state, stunned):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        explosionRadius()


@registerEvent(AmmoReplayPlayer, 'setGunReloadTime')
def AmmoReplayPlayer_setGunReloadTime(self, timeLeft, baseTime):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        explosionRadius()


@registerEvent(CrosshairPanelContainerMeta, 'as_setReloadingS')
def CrosshairPanelContainerMeta_as_setReloadingS(self, duration, baseTime, startTime, isReloading):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        explosionRadius()


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        if (not vInfoVO.isAlive()) and (vehicle is not None) and (vehicle.id == vInfoVO.vehicleID):
            global _explosionRadius, isDisplaySphere, isDownHotkey, isAlive
            _explosionRadius = None
            isDisplaySphere = False
            isDownHotkey = False
            isAlive = False


@registerEvent(PlayerAvatar, 'handleKey')
def handleKey(self, isDown, key, mods):
    if config.get('sight/enabled', True):# and isNotEvent:
        global isDownHotkey
        hotkey = config.get('sight/sphereDispersion/hotkey', None)
        if hotkey is not None and hotkey['enabled'] and (key == hotkey['keyCode']):
            if isDown:
                if hotkey['onHold']:
                    if not isDownHotkey:
                        isDownHotkey = True
                else:
                    isDownHotkey = not isDownHotkey
            else:
                if hotkey['onHold']:
                    if isDownHotkey:
                        isDownHotkey = False


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    if self.isPlayerVehicle and config.get('sight/enabled', True):
        global vehicle, _explosionRadius, isDisplaySphere, isDownHotkey, isAlive
        _explosionRadius = None
        if battle.isBattleTypeSupported:
            isAlive = self.isAlive
            vehicle = self
            vehClass = VEHICLE_CLASSES[list(self.typeDescriptor.type.tags.intersection(VEHICLE_CLASSES.keys()))[0]]
            isDisplaySphere = config.get('sight/sphereDispersion/enabled', False) and (vehClass in config.get('sight/sphereDispersion/vtype', ['SPG']))
            isDownHotkey = not config.get('sight/sphereDispersion/hotkey/enabled', False)


@registerEvent(Vehicle, 'onHealthChanged')
def onHealthChanged(self, newHealth, attackerID, attackReasonID):
    global isAlive
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        isAlive = self.isAlive()
        if (not isAlive) and (sphere in BigWorld.models()):
            BigWorld.delModel(sphere)


def update_sphere(position):
    global sphere
    if sphere is None:
        sphere = BigWorld.Model('objects/misc/bbox/sphere1.model')
    elif sphere in BigWorld.models():
        BigWorld.delModel(sphere)
    if (_explosionRadius is not None) and isAlive and isDownHotkey:
        sphere.position = position
        sphere.scale = Vector3(_explosionRadius, _explosionRadius, _explosionRadius)
        BigWorld.addModel(sphere)


@overrideMethod(VehicleGunRotator, '_VehicleGunRotator__getGunMarkerPosition')
def _VehicleGunRotator__getGunMarkerPosition(base, self, shotPos, shotVec, dispersionAngles):
    if not (config.get('sight/enabled', True) and battle.isBattleTypeSupported):
        return base(self, shotPos, shotVec, dispersionAngles)
    endPos, direction, markerDiameter, idealMarkerDiameter, collData = base(self, shotPos, shotVec, dispersionAngles)
    if isDisplaySphere:
        update_sphere(endPos)
    return endPos, direction, markerDiameter, idealMarkerDiameter, collData
