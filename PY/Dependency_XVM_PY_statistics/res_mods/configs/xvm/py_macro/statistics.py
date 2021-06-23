import time
import BigWorld
from Vehicle import Vehicle
import constants
from xfw.events import registerEvent
from xfw_actionscript.python import *
import xvm_main.python.userprefs as userprefs
import game
from datetime import datetime, timedelta
import BattleReplay
from predefined_hosts import g_preDefinedHosts
from xvm_main.python.logger import *
from messenger.proto.bw.ServiceChannelManager import ServiceChannelManager
from connection_mgr import ConnectionManager



startTimeSession = time.time()
countBattle = 0
countFinishedBattle = 0
isReplay = False
winsSession = 0
lossSession = 0
currentServer = None
data = userprefs.get('statistics/data', {'countBattleDay': 0,
                                         'timeDay': 0.0,
                                         'arenaUniqueID': None,
                                         'winsSessionDay': 0,
                                         'lossSessionDay': 0,
                                         'countFinishedBattleDay': 0,
                                         'date': 0})

REGION_RESET = {'NA': 11, 'EU': 5}

timeRealm = datetime.utcnow() - timedelta(hours=REGION_RESET.get(constants.CURRENT_REALM, 0))
if timeRealm.toordinal() == data['date']:
    countBattleDay = data.get('countBattleDay', 0)
    timeDay = data.get('timeDay', 0.0)
    arenaUniqueID = data.get('arenaUniqueID', None)
    winsSessionDay = data.get('winsSessionDay', 0)
    lossSessionDay = data.get('lossSessionDay', 0)
    countFinishedBattleDay = data.get('countFinishedBattleDay', 0)
else:
    winsSessionDay = 0
    lossSessionDay = 0
    countBattleDay = 0
    countFinishedBattleDay = 0
    timeDay = 0.0
    arenaUniqueID = None
    data['date'] = timeRealm.toordinal()

@registerEvent(game, 'fini')
def game_fini():
    if not isReplay:
        _timeRealm = datetime.utcnow() + timedelta(hours=REGION_RESET.get(constants.CURRENT_REALM, 0))
        if _timeRealm.toordinal() == data['date']:
            userprefs.set('statistics/data', {'countBattleDay': countBattleDay + countBattle,
                                              'timeDay': time.time() - startTimeSession + timeDay,
                                              'arenaUniqueID': arenaUniqueID,
                                              'winsSessionDay': winsSessionDay + winsSession,
                                              'lossSessionDay': lossSessionDay + lossSession,
                                              'countFinishedBattleDay': countFinishedBattleDay + countFinishedBattle,
                                              'date': _timeRealm.toordinal()})
        else:
            userprefs.set('statistics/data', {'countBattleDay': 0,
                                              'timeDay': 0.0,
                                              'arenaUniqueID': None,
                                              'winsSessionDay': 0,
                                              'lossSessionDay': 0,
                                              'countFinishedBattleDay': 0,
                                              'date': _timeRealm.toordinal()})


@registerEvent(ConnectionManager, '_ConnectionManager__connect')
def ConnectionManager__connect(self):
    global currentServer
    currentServer = self.serverUserNameShort


@registerEvent(ServiceChannelManager, '_ServiceChannelManager__addServerMessage')
def ServiceChannelManager__addServerMessage(self, message):
    global winsSession, lossSession, countFinishedBattle
    if (countBattle > 0) or (countBattleDay > 0):
        if message.type == 2:
            countFinishedBattle += 1
            if message.data.get('isWinner', 0) == 1:
                winsSession += 1
            elif message.data.get('isWinner', 0) == -1:
                lossSession += 1
            as_event('ON_STATISTICS')


@registerEvent(Vehicle, '_Vehicle__onAppearanceReady')
def _Vehicle__onAppearanceReady(self, appearance):
    global arenaUniqueID, countBattle, isReplay
    if self.isPlayerVehicle:
        isReplay = BattleReplay.isPlaying()
        if (arenaUniqueID != BigWorld.player().arenaUniqueID) or (arenaUniqueID is None):
            arenaUniqueID = BigWorld.player().arenaUniqueID
            countBattle += 1


def timeSession(t):
    t = int(t)
    s = t % 60
    t = int((t - s) / 60)
    m = t % 60
    h = int((t - m) / 60)
    return h, m, s


@xvm.export('xvm.timeSession', deterministic=False)
def xvm_timeSession():
    h, m, _ = timeSession(time.time() - startTimeSession)
    return '{:02d}:{:02d}'.format(h, m)


@xvm.export('xvm.timeSessionS', deterministic=False)
def xvm_timeSessionS():
    h, m, s = timeSession(time.time() - startTimeSession)
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


@xvm.export('xvm.countBattle')
def xvm_countBattle():
    return countBattle


@xvm.export('xvm.timeSessionDay', deterministic=False)
def xvm_timeSessionDay():
    h, m, _ = timeSession(time.time() - startTimeSession + timeDay)
    return '{:02d}:{:02d}'.format(h, m)


@xvm.export('xvm.timeSessionSDay', deterministic=False)
def xvm_timeSessionSDay():
    h, m, s = timeSession(time.time() - startTimeSession + timeDay)
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


@xvm.export('xvm.countBattleDay')
def xvm_countBattleDay():
    return countBattle + countBattleDay


@xvm.export('xvm.winsSession')
def xvm_winsSession():
    return winsSession


@xvm.export('xvm.lossSession')
def xvm_lossSession():
    return lossSession


@xvm.export('xvm.lossSessionDay')
def xvm_lossSessionDay():
    return lossSession + lossSessionDay


@xvm.export('xvm.winsSessionDay')
def xvm_winsSessionDay():
    return winsSessionDay + winsSession


@xvm.export('xvm.currentServer')
def xvm_currentServer():
    return currentServer


@xvm.export('xvm.winRateSession')
def xvm_winRateSession():
    if countFinishedBattle == 0:
        return None
    else:
        return float(100 * winsSession / float(countFinishedBattle))


@xvm.export('xvm.winRateSessionDay')
def xvm_winRateSessionDay():
    if (countFinishedBattle + countFinishedBattleDay) == 0:
        return None
    else:
        return float(100 * (winsSessionDay + winsSession) / float(countFinishedBattle + countFinishedBattleDay))
