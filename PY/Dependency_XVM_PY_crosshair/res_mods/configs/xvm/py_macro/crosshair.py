import GUI
from Avatar import PlayerAvatar
from AvatarInputHandler.AimingSystems import shootInSkyPoint
from AvatarInputHandler.cameras import getWorldRayAndPoint
from BigWorld import callback, cancelCallback
from ProjectileMover import collideDynamicAndStatic
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats

import xvm_battle.python.battle as battle
from xfw.events import registerEvent
from xfw_actionscript.python import *
from xvm_main.python.logger import *

distance = None
ownVehicle = None
getDistanceID = None


def getDistance():
    global distance, getDistanceID
    if ownVehicle is not None:
        pos = GUI.mcursor().position
        direction, start = getWorldRayAndPoint(*pos)
        end = start + direction.scale(100000.0)
        point = collideDynamicAndStatic(start, end, (ownVehicle.id,), 0)
        aimingPoint = point[0] if point is not None else shootInSkyPoint(start, direction)
        prevDistance = distance
        distance = int((aimingPoint - ownVehicle.position).length)
        if prevDistance != distance:
            as_event('ON_CROSSHAIR')
        getDistanceID = callback(0.1, getDistance)


def reset():
    global ownVehicle, getDistanceID, distance
    ownVehicle = None
    if getDistanceID is not None:
        cancelCallback(getDistanceID)
        getDistanceID = None
    distance = None


@registerEvent(Vehicle, 'onEnterWorld')
def onEnterWorld(self, prereqs):
    global ownVehicle, getDistanceID
    if self.isPlayerVehicle and self.isAlive() and battle.isBattleTypeSupported:
        ownVehicle = self
        getDistanceID = callback(0.1, getDistance)


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    if not vInfoVO.isAlive() and ownVehicle is not None and (ownVehicle.id == vInfoVO.vehicleID) and battle.isBattleTypeSupported:
        reset()
        as_event('ON_CROSSHAIR')


@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    reset()


@xvm.export('sight.distCrosshair', deterministic=False)
def sight_distCrosshair():
    return distance
