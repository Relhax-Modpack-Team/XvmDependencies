from Vehicle import Vehicle

from xfw.events import registerEvent
from xfw_actionscript.python import *

health = 0
maxHealth = 0
oldHealth = 0
dmg = None
vehicle = None


@registerEvent(Vehicle, 'onHealthChanged')
def onHealthChanged(self, newHealth, attackerID, attackReasonID):
    if self.isPlayerVehicle:
        global health, dmg, oldHealth
        health = max(0, newHealth)
        if oldHealth != health:
            dmg = oldHealth - health
            oldHealth = health
        as_event('ON_MY_HP')


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global maxHealth, health, vehicle, dmg, oldHealth
    if self.isPlayerVehicle:
        maxHealth = self.maxHealth
        oldHealth = maxHealth
        health = self.health
        vehicle = self
        dmg = None
        as_event('ON_MY_HP')


@xvm.export('my_hp.health', deterministic=False)
def my_hp_health(_health=None):
    if health is not None:
        if maxHealth != 0:
            return health if _health is None else int(_health * health // maxHealth)
        else:
            return health if _health is None else _health


@xvm.export('my_hp.maxHealth', deterministic=False)
def my_hp_maxHealth():
    return maxHealth


@xvm.export('my_hp.dmg', deterministic=False)
def my_hp_dmg():
    return dmg
