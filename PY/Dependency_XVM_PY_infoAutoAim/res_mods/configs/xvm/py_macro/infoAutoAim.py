import BigWorld
import Math
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from vehicle_systems.tankStructure import TankPartIndexes
from gui.battle_control import event_dispatcher


from xfw.events import registerEvent, overrideMethod
from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *


targetName = None
targetVehicle = None
targetHealth = None
targetID = None
playerVehicleID = None
marker = None
isShowAutoAimMarker = False


class Arrow(object):

    def __init__(self):
        try:
            self.__model = BigWorld.Model(
                '../mods/shared_resources/xvm/res/markers/Arrow/arrow.model')
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


@registerEvent(PlayerAvatar, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global targetName, targetVehicle, targetHealth, playerVehicleID, targetID, marker, isShowAutoAimMarker
    if config.get('sight/enabled', True):
        if config.get('sight/autoAim/enabled', False):
            vehicle = BigWorld.entity(self.playerVehicleID)
            value = config.get(
                'sight/autoAim/showAutoAimMarker', 'wheels').lower()
            isShowAutoAimMarker = vehicle.isWheeledTech if value not in [
                'all', 'none'] else (value == 'all')
            markerType = config.get('sight/autoAim/markerType', '')
            if markerType.strip().lower() == 'cylinder':
                marker = Cylinder()
            elif markerType.strip().lower() == 'arrow':
                marker = Arrow()
            else:
                marker = None
        else:
            marker = None
        targetName = None
        targetVehicle = None
        targetHealth = None
        targetID = None
        playerVehicleID = self.playerVehicleID


@registerEvent(Vehicle, 'onHealthChanged')
def onHealthChanged(self, newHealth, attackerID, attackReasonID):
    global targetHealth
    if config.get('sight/enabled', True):
        if targetID is not None and targetID == self.id:
            targetHealth = self.health
            as_event('ON_AUTO_AIM')


@registerEvent(PlayerAvatar, 'onLockTarget')
def onLockTarget(self, state, playVoiceNotifications):
    global targetName, targetVehicle, targetHealth, targetID, marker
    if config.get('sight/enabled', True):
        target = BigWorld.target()
        if (state == 1) and target is not None:
            targetVehicle = target.typeDescriptor.type.shortUserString
            targetName = target.publicInfo.name
            targetHealth = target.health
            targetID = target.id
            if isShowAutoAimMarker:
                event_dispatcher.addAutoAimMarker(target)
            else:
                event_dispatcher.hideAutoAimMarker()
            if marker is not None:
                marker.showMarker(target)
        else:
            targetName = None
            targetVehicle = None
            targetHealth = None
            targetID = None
            if isShowAutoAimMarker:
                event_dispatcher.hideAutoAimMarker()
            if marker is not None:
                marker.hideMarker()
        as_event('ON_AUTO_AIM')


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    global targetName, targetVehicle, targetHealth, targetID
    if config.get('sight/enabled', True) and (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID):
        targetName = None
        targetVehicle = None
        targetHealth = None
        targetID = None
        if marker is not None:
            marker.hideMarker()
        as_event('ON_AUTO_AIM')


@xvm.export('sight.autoAimName', deterministic=False)
def sight_autoAimName():
    return targetName


@xvm.export('sight.autoAimVehicle', deterministic=False)
def sight_autoAimVehicle():
    return targetVehicle


@xvm.export('sight.autoAimHealth', deterministic=False)
def sight_autoAimHealth():
    return targetHealth
