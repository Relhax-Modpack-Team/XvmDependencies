from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.Scaleform.daapi.view.meta.PostmortemPanelMeta import PostmortemPanelMeta

from xfw import *
from xfw_actionscript.python import *

health = 0
maxHealth = 0
vehicle = None


@registerEvent(Vehicle, 'onHealthChanged')
def onHealthChanged(self, newHealth, attackerID, attackReasonID):
    if self.isPlayerVehicle:
        global health
        health = max(0, newHealth)
        as_event('ON_MY_HP')


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global maxHealth, health, vehicle
    if self.isPlayerVehicle:
        maxHealth = self.typeDescriptor.maxHealth
        health = self.health
        vehicle = self
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
