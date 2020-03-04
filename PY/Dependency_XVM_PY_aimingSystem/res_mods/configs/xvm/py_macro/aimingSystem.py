import BigWorld
from account_helpers.settings_core.options import InterfaceScaleSetting
from Avatar import PlayerAvatar
from AvatarInputHandler.AimingSystems.ArcadeAimingSystem import ArcadeAimingSystem
from AvatarInputHandler.AimingSystems.SniperAimingSystem import SniperAimingSystem
from AvatarInputHandler.AimingSystems.StrategicAimingSystem import StrategicAimingSystem
import gui.Scaleform.daapi.view.battle.shared.crosshair.plugins as plug

from xfw.events import registerEvent, overrideMethod
import xvm_battle.python.battle as battle
from xfw_actionscript.python import *
from xvm_main.python.logger import *

ARCADE_MODE = 'arc'
SNIPER_MODE = 'sn'
STRATEGIC_MODE = 'str'
SHIFT = 0.0775
NETS_TYPES = {0: 'diagonal', 1: 'horizontal', 2: 'radial', 3: 'dotted'}

aimMode = ARCADE_MODE
y = 0.0
netType = {ARCADE_MODE: 0, SNIPER_MODE: 0}

@registerEvent(ArcadeAimingSystem, 'enable')
def ArcadeAimingSystem_enable(self, targetPos, turretYaw=None, gunPitch=None):
    if battle.isBattleTypeSupported:
        global y, aimMode
        y = - BigWorld.screenHeight() * SHIFT
        aimMode = ARCADE_MODE
        as_event('ON_AIM_MODE')


@registerEvent(SniperAimingSystem, 'enable')
def SniperAimingSystem_enable(self, targetPos, playerGunMatFunction):
    if battle.isBattleTypeSupported:
        global y, aimMode
        y = 0.0
        aimMode = SNIPER_MODE
        as_event('ON_AIM_MODE')


@registerEvent(StrategicAimingSystem, 'enable')
def StrategicAimingSystem_enable(self, targetPos):
    if battle.isBattleTypeSupported:
        global y, aimMode
        y = 0.0
        aimMode = STRATEGIC_MODE
        as_event('ON_AIM_MODE')


@registerEvent(InterfaceScaleSetting, 'setSystemValue')
def InterfaceScaleSetting_setSystemValue(self, value):
    if battle.isBattleTypeSupported:
        global y
        y = - BigWorld.screenHeight() * SHIFT if aimMode == ARCADE_MODE else 0.0
        as_event('ON_AIM_MODE')


@registerEvent(PlayerAvatar, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global y, aimMode
    if battle.isBattleTypeSupported:
        y = - BigWorld.screenHeight() * SHIFT
        aimMode = ARCADE_MODE
        as_event('ON_AIM_MODE')


@overrideMethod(plug, '_makeSettingsVO')
def plugins_makeSettingsVO(base, settingsCore, *keys):
    data = base(settingsCore, *keys)
    if 1 in data:
        netType[ARCADE_MODE] = data[1].get('netType', None)
    if 2 in data:
        netType[SNIPER_MODE] = data[2].get('netType', None)
    as_event('ON_AIM_MODE')
    return data


@xvm.export('aim.mode', deterministic=False)
def aim_mode(arc=ARCADE_MODE, sn=SNIPER_MODE, strat=STRATEGIC_MODE):
    if aimMode == ARCADE_MODE:
        return arc
    elif aimMode == SNIPER_MODE:
        return sn
    elif aimMode == STRATEGIC_MODE:
        return strat


@xvm.export('aim.y', deterministic=False)
def aim_y(shift=0.0):
    return int(y + shift)


@xvm.export('aim.netType', deterministic=False)
def aim_netType(*args):
    currentNet = netType.get(aimMode, None)
    if currentNet is None:
        return None
    return args[currentNet] if currentNet < len(args) else NETS_TYPES[currentNet]
