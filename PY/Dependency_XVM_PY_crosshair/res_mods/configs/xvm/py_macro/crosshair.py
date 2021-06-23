import GUI
from Avatar import PlayerAvatar
from AvatarInputHandler import AvatarInputHandler
from AvatarInputHandler.AimingSystems import shootInSkyPoint
from AvatarInputHandler.cameras import getWorldRayAndPoint
from BigWorld import callback, cancelCallback
from ProjectileMover import collideDynamicAndStatic
from Vehicle import Vehicle
from aih_constants import CTRL_MODE_NAME

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
from xfw.events import registerEvent
from xfw_actionscript.python import *
from xvm_main.python.logger import *

distance = None
ownVehicle = None
getDistanceID = None
visible = True
DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]


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


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    newVisible = eMode in DISPLAY_IN_MODES
    if newVisible != visible:
        visible = newVisible
        as_event('ON_CROSSHAIR')


@registerEvent(Vehicle, '_Vehicle__onAppearanceReady')
def _Vehicle__onAppearanceReady(self, appearance):
    global ownVehicle, getDistanceID, visible
    if self.isPlayerVehicle and config.get('sight/enabled', True) and self.isAlive() and battle.isBattleTypeSupported:
        ownVehicle = self
        visible = True
        getDistanceID = callback(0.1, getDistance)


@registerEvent(PlayerAvatar, 'updateVehicleHealth')
def PlayerAvatar_updateVehicleHealth(self, vehicleID, health, deathReasonID, isCrewActive, isRespawn):
    if not (health > 0 and isCrewActive) and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        reset()
        as_event('ON_CROSSHAIR')


@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    reset()


@xvm.export('sight.distCrosshair', deterministic=False)
def sight_distCrosshair():
    return distance if visible else None
