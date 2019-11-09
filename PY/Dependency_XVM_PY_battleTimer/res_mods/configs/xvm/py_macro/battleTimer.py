from Avatar import PlayerAvatar
from Vehicle import Vehicle
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider
from gui.Scaleform.daapi.view.battle.shared.battle_timers import BattleTimer
from gui.Scaleform.daapi.view.battle.epic.battle_timer import EpicBattleTimer

from xfw import *
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle

minutes = None
seconds = None
startBattle = 0
arenaPeriod = None


def updateTime(_minutes, _seconds):
    global minutes, seconds
    if battle.isBattleTypeSupported:
        if startBattle not in [2, 3]:
            _minutes, _seconds = None, None
        if minutes != _minutes or seconds != _seconds:
            minutes, seconds = _minutes, _seconds
        as_event('ON_BATTLE_TIMER')


@registerEvent(EpicBattleTimer, '_sendTime')
def BattleTimer_sendTime(self, _minutes, _seconds):
    updateTime(_minutes, _seconds)


@registerEvent(BattleTimer, '_sendTime')
def BattleTimer_sendTime(self, _minutes, _seconds):
    updateTime(_minutes, _seconds)


@registerEvent(PlayerAvatar, '_PlayerAvatar__onArenaPeriodChange')
def PlayerAvatar__onArenaPeriodChange(self, period, periodEndTime, periodLength, periodAdditionalInfo):
    global startBattle
    if startBattle != period and battle.isBattleTypeSupported:
        startBattle = period
        as_event('ON_BATTLE_TIMER')


@registerEvent(Vehicle, 'onEnterWorld')
def onEnterWorld(self, prereqs):
    global minutes, seconds, startBattle
    if self.isPlayerVehicle and battle.isBattleTypeSupported:
        sessionProvider = dependency.instance(IBattleSessionProvider)
        minutes = None
        seconds = None
        startBattle = sessionProvider.shared.arenaPeriod.getPeriod()


@xvm.export('xvm.minutesBT', deterministic=False)
def xvm_minutesBT():
    return minutes


@xvm.export('xvm.secondsBT', deterministic=False)
def xvm_secondsBT():
    return seconds


@xvm.export('xvm.critTimeBT', deterministic=False)
def xvm_critTimeBT(_critTime=120):
    if seconds is None:
        return None
    return '#FF0000' if (_critTime > (minutes * 60 + seconds)) and (startBattle == 3) else None
