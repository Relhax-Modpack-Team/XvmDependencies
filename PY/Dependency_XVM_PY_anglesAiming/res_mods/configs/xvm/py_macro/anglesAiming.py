from BigWorld import player, screenHeight, screenWidth, cancelCallback, projection, callback, wg_calcGunPitchLimits, getAspectRatio
from Vehicle import Vehicle
import GUI
from math import pi, degrees
from AvatarInputHandler import MapCaseMode
from AvatarInputHandler.cameras import FovExtended
from AvatarInputHandler.AimingSystems.ArcadeAimingSystem import ArcadeAimingSystem
from AvatarInputHandler.AimingSystems.SniperAimingSystem import SniperAimingSystem
from AvatarInputHandler.AimingSystems.StrategicAimingSystem import StrategicAimingSystem


from xfw.events import registerEvent
from xvm_main.python.logger import *
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle


COUNT_STEPS = 3.0
STEP = 1.0 / COUNT_STEPS
TIME_STEP = 0.1 / COUNT_STEPS
YAW_STEP_CORNER = pi / 512
COORDINATE_OFF_SCREEN = 20000


pitchStep = 0
yaw = old_yaw = 0.0
pitch = old_pitch = 0.0
old_multiplier = 1.0
dataHor = [-COORDINATE_OFF_SCREEN, COORDINATE_OFF_SCREEN]
dataVert = [COORDINATE_OFF_SCREEN, -COORDINATE_OFF_SCREEN]
leftLimits, rightLimits = 0, 0
maxPitch = None
minPitch = None
scaleHor = None
scaleVert = None
yVert = 0
currentStepYaw = 0
currentStepPitch = 0
isAlive = False
showHorCorners = False
showVerCorners = False
showCorners = False
isMapCas = False
old_gunAnglesPacked = 0
smoothingID = None
visible = True
turretPitch = 0.0
gunJointPitch = 0.0


def hideCorners():
    global dataHor, dataVert
    dataHor = [-COORDINATE_OFF_SCREEN, COORDINATE_OFF_SCREEN]
    dataVert = [COORDINATE_OFF_SCREEN, -COORDINATE_OFF_SCREEN]


@registerEvent(MapCaseMode, 'activateMapCase')
def anglesAiming_activateMapCase(equipmentID, deactivateCallback, isArcadeCamera=False):
    global isMapCas
    isMapCas = True
    hideCorners()
    as_event('ON_ANGLES_AIMING')


@registerEvent(MapCaseMode, 'turnOffMapCase')
def anglesAiming_turnOffMapCase(equipmentID, isArcadeCamera=False):
    global isMapCas
    isMapCas = False


@registerEvent(ArcadeAimingSystem, 'enable')
def ArcadeAimingSystem_enable(self, targetPos, turretYaw=None, gunPitch=None):
    global yVert
    if battle.isBattleTypeSupported:
        yVert = - screenHeight() * 0.0775
        updateCoordinates()


@registerEvent(SniperAimingSystem, 'enable')
def SniperAimingSystem_enable(self, targetPos, playerGunMatFunction):
    global yVert
    if battle.isBattleTypeSupported:
        yVert = 0
        updateCoordinates()


@registerEvent(StrategicAimingSystem, 'enable')
def StrategicAimingSystem_enable(self, targetPos):
    global yVert
    if battle.isBattleTypeSupported:
        yVert = 0
        updateCoordinates()


@registerEvent(Vehicle, 'onEnterWorld')
def onEnterWorld(self, prereqs):
    if self.isPlayerVehicle:
        global yaw, old_yaw, pitch, old_pitch, old_multiplier, leftLimits, rightLimits, smoothingID
        global pitchStep, maxPitch, minPitch, minBound, maxBound, visible, isMapCas, turretPitch, gunJointPitch
        global old_gunAnglesPacked, isAlive, showHorCorners, showVerCorners, showCorners
        if battle.isBattleTypeSupported:
            # log('%s x %s    %s x %s' % (screenWidth(), screenHeight(), GUI.screenResolution()[0], GUI.screenResolution()[1]))
            smoothingID = None
            yaw = old_yaw = 0.0
            pitch = old_pitch = 0.0
            old_multiplier = 1.0
            old_gunAnglesPacked = 0
            isAlive = self.isAlive
            gun = self.typeDescriptor.gun
            minBound, maxBound = gun.pitchLimits['absolute']
            pitchStep = (maxBound - minBound) / 63.0
            showHorCorners = not ((gun.staticTurretYaw is not None) or (gun.turretYawLimits is None))
            if showHorCorners:
                leftLimits, rightLimits = gun.turretYawLimits
            else:
                leftLimits, rightLimits = None, None
            showVerCorners = not gun.staticPitch
            showCorners = showHorCorners or showVerCorners
            isMapCas = False
            maxPitch = gun.pitchLimits['maxPitch']
            minPitch = gun.pitchLimits['minPitch']
            visible = True
            turretPitch = self.typeDescriptor.hull.turretPitches[0]
            gunJointPitch = self.typeDescriptor.turret.gunJointPitch
            updateCoordinates()


@registerEvent(Vehicle, '_Vehicle__onVehicleDeath')
def Vehicle__onVehicleDeath(self, isDeadStarted=False):
    if self.isPlayerVehicle and battle.isBattleTypeSupported:
        global dataHor, dataVert, isAlive, showCorners
        isAlive = False
        hideCorners()
        showCorners = False
        as_event('ON_ANGLES_AIMING')


@registerEvent(Vehicle, 'set_gunAnglesPacked')
def set_gunAnglesPacked(self, prev):
    global yaw, old_yaw, pitch, old_pitch, old_gunAnglesPacked, dataHor, dataVert, smoothingID, currentStepPitch, currentStepYaw
    if self.isPlayerVehicle and (self.gunAnglesPacked != old_gunAnglesPacked) and battle.isBattleTypeSupported and showCorners and not isMapCas:
        if player() is not None and not player().isObserver():
            _pitch = self.gunAnglesPacked & 63
            if ((old_gunAnglesPacked & 63) == _pitch) and not showHorCorners:
                return
            old_gunAnglesPacked = self.gunAnglesPacked
            yaw = YAW_STEP_CORNER * (self.gunAnglesPacked >> 6 & 1023) - pi
            pitch = minBound + _pitch * pitchStep
            currentStepPitch = (pitch - old_pitch) * STEP
            currentStepYaw = (yaw - old_yaw) * STEP
            if smoothingID is not None:
                cancelCallback(smoothingID)
                smoothingID = None
            smoothing(old_yaw + currentStepYaw, old_pitch + currentStepPitch, STEP)
            old_yaw = 0 if not showHorCorners else yaw
            old_pitch = pitch
        else:
            hideCorners()


@registerEvent(FovExtended, 'setFovByMultiplier')
def setFovByMultiplier(self, multiplier, rampTime=None):
    global old_multiplier
    if (old_multiplier != multiplier) and showCorners and battle.isBattleTypeSupported and not isMapCas:
        old_multiplier = multiplier
        updateCoordinates()


def updateLabels():
    global visible
    halfScreenW = screenWidth() / 2
    halfScreenH = screenHeight() / 2
    left, right = dataHor
    bottom, top = dataVert
    old_visible = visible
    if showHorCorners:
        visible = not ((left < - halfScreenW) and (right > halfScreenW) and (top < -halfScreenH) and (bottom > halfScreenH))
    else:
        visible = not ((top < -halfScreenH) and (bottom > halfScreenH))
    if visible or old_visible:
        as_event('ON_ANGLES_AIMING')


def updateCoordinates():
    global dataHor, dataVert, scaleHor, scaleVert, smoothingID
    if isMapCas:
        return
    if smoothingID is not None:
        cancelCallback(smoothingID)
        smoothingID = None
    verticalFov = projection().fov
    horizontalFov = verticalFov * getAspectRatio()
    screenW = screenWidth()
    screenH = screenHeight()
    scaleHor = screenW / horizontalFov if horizontalFov else screenW
    scaleVert = screenH / verticalFov if verticalFov else screenH
    dataHor, dataVert = coordinate(yaw, pitch)
    updateLabels()


def smoothing(stepYaw, stepPitch, step):
    global dataHor, dataVert, smoothingID
    dataHor, dataVert = coordinate(stepYaw, stepPitch)
    if (step + STEP) < 1.001:
        smoothingID = callback(TIME_STEP, lambda: smoothing(stepYaw + currentStepYaw, stepPitch + currentStepPitch, step + STEP))
    else:
        smoothingID = None
    updateLabels()


def coordinate(_yaw, _pitch):
    if showHorCorners:
        dif_yaw = leftLimits - _yaw
        xLeft = int(scaleHor * dif_yaw) if dif_yaw < -YAW_STEP_CORNER else 0
        dif_yaw = rightLimits - _yaw
        xRight = int(scaleHor * dif_yaw) if dif_yaw > YAW_STEP_CORNER else 0
    else:
        xLeft = - COORDINATE_OFF_SCREEN
        xRight = COORDINATE_OFF_SCREEN
    if showVerCorners:
        pTop, pBottom = wg_calcGunPitchLimits(_yaw, minPitch, maxPitch, turretPitch, gunJointPitch)
        dif_pitch = pBottom - _pitch
        yBottom = int((scaleVert * dif_pitch + yVert) if dif_pitch > pitchStep else yVert)
        dif_pitch = pTop - _pitch
        yTop = int((scaleVert * dif_pitch + yVert) if dif_pitch < -pitchStep else yVert)
    else:
        yBottom = COORDINATE_OFF_SCREEN
        yTop = -COORDINATE_OFF_SCREEN
    return [xLeft, xRight], [yBottom, yTop]


@xvm.export('anglesAiming.left', deterministic=False)
def xvm_anglesAiming_xLeft(x=0):
    left = dataHor[0]
    return (left + x) if isAlive else - COORDINATE_OFF_SCREEN


@xvm.export('anglesAiming.right', deterministic=False)
def xvm_anglesAiming_xRight(x=0):
    right = dataHor[1]
    return (right + x) if isAlive else COORDINATE_OFF_SCREEN


@xvm.export('anglesAiming.bottom', deterministic=False)
def xvm_anglesAiming_yBottom(y=0):
    bottom = dataVert[0]
    return (bottom + y) if isAlive else COORDINATE_OFF_SCREEN


@xvm.export('anglesAiming.top', deterministic=False)
def xvm_anglesAiming_yTop(y=0):
    top = dataVert[1]
    return (top + y) if isAlive else - COORDINATE_OFF_SCREEN


@xvm.export('anglesAiming.yaw', deterministic=False)
def xvm_anglesAiming_yaw():
    return degrees(stepYaw) if isAlive else None


@xvm.export('anglesAiming.yawLeft', deterministic=False)
def xvm_anglesAiming_yawLeft():
    return degrees(leftLimits) if showHorCorners and isAlive else None


@xvm.export('anglesAiming.yawRight', deterministic=False)
def xvm_anglesAiming_yawRight():
    return degrees(rightLimits) if showHorCorners and isAlive else None


@xvm.export('anglesAiming.pitch', deterministic=False)
def xvm_anglesAiming_pitch():
    return degrees(pitch) if isAlive else None


@xvm.export('anglesAiming.pitchMax', deterministic=False)
def xvm_anglesAiming_pitchMax():
    return degrees(maxBound) if isAlive else None


@xvm.export('anglesAiming.pitchMin', deterministic=False)
def xvm_anglesAiming_pitchMin():
    return degrees(minBound) if isAlive else None
