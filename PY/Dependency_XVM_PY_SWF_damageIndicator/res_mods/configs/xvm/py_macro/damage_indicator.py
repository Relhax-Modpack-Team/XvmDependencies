from math import pi

import BigWorld
from AvatarInputHandler.control_modes import ArcadeControlMode, SniperControlMode, StrategicControlMode
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.shared.indicators import _DamageIndicator, DamageIndicatorMeta

from xfw.events import registerEvent, overrideMethod
from xfw_actionscript.python import *
from xvm_main.python.logger import *

alpha = 0
di = {}
di1 = []
aim = None


@registerEvent(ArcadeControlMode, 'handleMouseEvent')
def arcadeHandleMouseEvent(self, dx, dy, dz):
    global aim
    if di:
        for value in di.values():
            angle = BigWorld.camera().direction.yaw + pi - value
            if (angle >= 0.01) or (angle <= -0.01):
                angle -= 2 * pi
            if (angle <= 0.01) and (angle >= -0.01):
                if aim is None:
                    aim = 'aim'
                    as_event('ON_DAMAGE_INDICATOR')
                return
        if aim is not None:
            aim = None
            as_event('ON_DAMAGE_INDICATOR')


@registerEvent(StrategicControlMode, 'handleMouseEvent')
def strategicHandleMouseEvent(self, dx, dy, dz):
    global aim
    if di:
        for value in di.values():
            angle = BigWorld.camera().direction.yaw + pi - value
            if (angle >= 0.01) or (angle <= -0.01):
                angle -= 2 * pi
            if (angle <= 0.01) and (angle >= -0.01):
                if aim is None:
                    aim = 'aim'
                    as_event('ON_DAMAGE_INDICATOR')
                return
        if aim is not None:
            aim = None
            as_event('ON_DAMAGE_INDICATOR')


@registerEvent(SniperControlMode, 'handleMouseEvent')
def sniperHandleMouseEvent(self, dx, dy, dz):
    global aim
    if di:
        for value in di.values():
            angle = BigWorld.camera().direction.yaw + pi - value
            if (angle >= 0.01) or (angle <= -0.01):
                angle -= 2 * pi
            if (angle <= 0.01) and (angle >= -0.01):
                if aim is None:
                    aim = 'aim'
                    as_event('ON_DAMAGE_INDICATOR')
                return
        if aim is not None:
            aim = None
            as_event('ON_DAMAGE_INDICATOR')


@overrideMethod(_DamageIndicator, 'getDuration')
def _DamageIndicator_getDuration(base, self):
    return 12


@registerEvent(_DamageIndicator, 'showHitDirection')
def _DamageIndicator_showHitDirection(self, idx, hitData, timeLeft):
    global alpha, di
    di[idx] = hitData.getYaw()
    if alpha == 0:
        alpha = 100
        as_event('ON_DAMAGE_INDICATOR')


@registerEvent(_DamageIndicator, 'hideHitDirection')
def _DamageIndicator_hideHitDirection(self, idx):
    global alpha, di
    if idx in di:
        del di[idx]
    if not di and (alpha == 100):
        alpha = 0
        as_event('ON_DAMAGE_INDICATOR')


@registerEvent(Vehicle, '_Vehicle__onAppearanceReady')
def _Vehicle__onAppearanceReady(self, appearance):
    if self.isPlayerVehicle:
        global alpha, aim, di
        di = {}
        alpha = 0
        aim = None
        as_event('ON_DAMAGE_INDICATOR')


@xvm.export('xvm.damageIndicator', deterministic=False)
def xvm_damageIndicator():
    return alpha


@xvm.export('xvm.damageIndicator_aim', deterministic=False)
def xvm_damageIndicator_aim():
    return aim
