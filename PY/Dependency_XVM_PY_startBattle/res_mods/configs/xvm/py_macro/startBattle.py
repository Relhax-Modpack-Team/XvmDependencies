import BigWorld
from xfw import *
from gui.Scaleform.daapi.view.battle.shared.battle_timers import BattleTimer
from Vehicle import Vehicle
from xfw_actionscript.python import *


startBattle = 0
arenaPeriod = None


@registerEvent(BattleTimer, 'setTotalTime')
def setTotalTime(self, totalTime):
    global startBattle
    startBattle = arenaPeriod.getPeriod() if arenaPeriod is not None else 0
    as_event('ON_BATTLE_TIMER')


@registerEvent(Vehicle, 'onEnterWorld')
def onEnterWorld(self, prereqs):
    global startBattle, arenaPeriod
    if self.isPlayerVehicle:
        startBattle = 0
        player = BigWorld.player()
        arenaPeriod = player.guiSessionProvider.shared.arenaPeriod


@xvm.export('xvm.startBattle', deterministic=False)
def xvm_startBattle():
    return startBattle

