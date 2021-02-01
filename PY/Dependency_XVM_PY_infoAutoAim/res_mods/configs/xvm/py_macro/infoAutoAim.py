import BattleReplay
import BigWorld
import gui.Scaleform.daapi.view.battle.shared.markers2d.plugins as plug
from Avatar import PlayerAvatar
from AvatarInputHandler import AvatarInputHandler
from Vehicle import Vehicle
from aih_constants import CTRL_MODE_NAME
from constants import AIMING_MODE
from vehicle_systems.tankStructure import TankPartIndexes

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
from xfw.events import registerEvent
from xfw_actionscript.python import *
from xvm_main.python.logger import *

targetName = None
targetVehicle = None
targetHealth = None
targetID = None
playerVehicleID = None
marker = None
visible = True

DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]


class Arrow(object):

    def __init__(self):
        try:
            self.__model = BigWorld.Model('../mods/shared_resources/xvm/res/markers/Arrow/arrow.model')
        except:
            self.__model = None
        self.__motor = None

    def hideMarker(self):
        global marker
        if self.__model in BigWorld.models():
            self.__model.delMotor(self.__motor)
            BigWorld.delModel(self.__model)

    def showMarker(self, target):
        if self.__model is not None:
            self.hideMarker()
            if target is not None:
                self.__motor = BigWorld.Servo(target.matrix)
                self.__model.addMotor(self.__motor)
                BigWorld.addModel(self.__model)


class Cylinder(object):

    def __init__(self):
        try:
            self.__modelBig = BigWorld.Model(
                '../mods/shared_resources/xvm/res/markers/cylinder/cylinder_red_big.model')
        except:
            self.__modelBig = None
        try:
            self.__modelMedium = BigWorld.Model(
                '../mods/shared_resources/xvm/res/markers/cylinder/cylinder_red_medium.model')
        except:
            self.__modelMedium = None
        try:
            self.__modelSmall = BigWorld.Model(
                '../mods/shared_resources/xvm/res/markers/cylinder/cylinder_red_small.model')
        except:
            self.__modelSmall = None
        self.__motor = None

    def hideMarker(self):
        if self.__modelSmall in BigWorld.models():
            self.__modelSmall.delMotor(self.__motor)
            BigWorld.delModel(self.__modelSmall)
        if self.__modelMedium in BigWorld.models():
            self.__modelMedium.delMotor(self.__motor)
            BigWorld.delModel(self.__modelMedium)
        if self.__modelBig in BigWorld.models():
            self.__modelBig.delMotor(self.__motor)
            BigWorld.delModel(self.__modelBig)

    def showMarker(self, target):
        if target is None:
            return
        vehicleLength = 0.0
        self.hideMarker()
        self.__motor = BigWorld.Servo(target.matrix)
        if target.appearance.collisions is not None:
            hullBB = target.appearance.collisions.getBoundingBox(
                TankPartIndexes.HULL)
            vehicleLength = abs(hullBB[1][2] - hullBB[0][2])
        if vehicleLength < 4.0:
            if self.__modelSmall is not None:
                self.__modelSmall.addMotor(self.__motor)
                BigWorld.addModel(self.__modelSmall)
        elif vehicleLength < 6.0:
            if self.__modelMedium is not None:
                self.__modelMedium.addMotor(self.__motor)
                BigWorld.addModel(self.__modelMedium)
        else:
            if self.__modelBig is not None:
                self.__modelBig.addMotor(self.__motor)
                BigWorld.addModel(self.__modelBig)


def resetTarget():
    global targetName, targetVehicle, targetHealth, targetID, marker
    targetName = None
    targetVehicle = None
    targetHealth = None
    targetID = None
    if marker is not None:
        marker.hideMarker()


def setTarget(vehicleID):
    global targetName, targetVehicle, targetHealth, targetID, marker
    target = BigWorld.entity(vehicleID)
    targetVehicle = target.typeDescriptor.type.shortUserString
    targetName = target.publicInfo.name
    targetHealth = target.health
    targetID = target.id
    if marker is not None:
        marker.showMarker(target)


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        newVisible = eMode in DISPLAY_IN_MODES
        if newVisible != visible:
            visible = newVisible
            as_event('ON_AUTO_AIM')


@registerEvent(PlayerAvatar, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global targetName, targetVehicle, targetHealth, playerVehicleID, targetID, marker, visible
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        marker = None
        if config.get('sight/autoAim/enabled', False):
            markerType = config.get('sight/autoAim/markerType', '')
            if markerType.strip().lower() == 'cylinder':
                marker = Cylinder()
            elif markerType.strip().lower() == 'arrow':
                marker = Arrow()
        targetName = None
        targetVehicle = None
        targetHealth = None
        targetID = None
        visible = True
        playerVehicleID = self.playerVehicleID


@registerEvent(Vehicle, 'onHealthChanged')
def onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID):
    global targetHealth
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        if targetID is not None and targetID == self.id:
            targetHealth = self.health
            if not self.isAlive():
                resetTarget()
            as_event('ON_AUTO_AIM')


@registerEvent(plug.VehicleMarkerTargetPlugin, '_VehicleMarkerTargetPlugin__addAutoAimMarker')
def VehicleMarkerTargetPlugin__addAutoAimMarker(self, event):
    if self._vehicleID is not None:
        setTarget(self._vehicleID)
        as_event('ON_AUTO_AIM')


@registerEvent(plug.VehicleMarkerTargetPlugin, '_addMarker')
def _addMarker(self, vehicleID):
    if BattleReplay.g_replayCtrl.isPlaying and vehicleID is not None:
        setTarget(vehicleID)
        as_event('ON_AUTO_AIM')

@registerEvent(AvatarInputHandler, 'setAimingMode')
def _setAimingMode(self, enable, mode):
    if mode == AIMING_MODE.TARGET_LOCK and not enable:
        resetTarget()
        as_event('ON_AUTO_AIM')


#
# @registerEvent(PlayerAvatar, 'onLockTarget')
# def onLockTarget(self, state, playVoiceNotifications):
#     global targetName, targetVehicle, targetHealth, targetID, marker
#     if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
#         log('PlayerAvatar state = %s' % state)
#         # target = BigWorld.target()
#         target = self.autoAimVehicle
#         if target is not None:
#             log('onLockTarget state = %s  target = %s' % (state, target.id))
#         else:
#             log('onLockTarget state = %s  target = %s' % (state, None))
#         if (state == 1) and target is not None:
#             targetVehicle = target.typeDescriptor.type.shortUserString
#             targetName = target.publicInfo.name
#             targetHealth = target.health
#             targetID = target.id
#             if marker is not None:
#                 marker.showMarker(target)
#         else:
#             resetTarget()
#         as_event('ON_AUTO_AIM')


# @registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
# def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
#     if config.get('sight/enabled', True) and (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID):
#         resetTarget()
#         as_event('ON_AUTO_AIM')


@xvm.export('sight.autoAimName', deterministic=False)
def sight_autoAimName():
    return targetName if visible else None


@xvm.export('sight.autoAimVehicle', deterministic=False)
def sight_autoAimVehicle():
    return targetVehicle if visible else None


@xvm.export('sight.autoAimHealth', deterministic=False)
def sight_autoAimHealth():
    return targetHealth if visible else None
