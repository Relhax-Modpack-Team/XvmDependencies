from Vehicle import Vehicle

from xfw.events import registerEvent
from xfw_actionscript.python import *

health = 0
maxHealth = 0
dmg = None
vehicle = None


@registerEvent(Vehicle, 'onHealthChanged')
def onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID):
    if self.isPlayerVehicle:
        global health, dmg
        health = max(0, newHealth)
        dmg = oldHealth - health
        as_event('ON_MY_HP')


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global maxHealth, health, vehicle, dmg
    if self.isPlayerVehicle:
        maxHealth = self.maxHealth
        health = self.health
        vehicle = self
        dmg = None
        as_event('ON_MY_HP')


@xvm.export('my_hp.health', deterministic=False)
def my_hp_health(norm=None):
    if health is not None:
        if maxHealth != 0:
            return health if norm is None else int(norm * health // maxHealth)
        else:
            return health if norm is None else norm


@xvm.export('my_hp.maxHealth', deterministic=False)
def my_hp_maxHealth():
    return maxHealth


@xvm.export('my_hp.dmg', deterministic=False)
def my_hp_dmg():
    return dmg
