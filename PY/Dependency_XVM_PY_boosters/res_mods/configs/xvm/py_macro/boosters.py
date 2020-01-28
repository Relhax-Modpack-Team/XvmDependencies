from helpers import time_utils
from helpers.i18n import makeString as _ms
from Account import PlayerAccount
from gui.shared.utils.requesters.ItemsRequester import REQ_CRITERIA
from helpers import dependency
from skeletons.gui.goodies import IGoodiesCache
from gui.goodies.goodie_items import _BOOSTER_TYPE_NAMES as BTN
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from gui.Scaleform.daapi.view.meta.LobbyHeaderMeta import LobbyHeaderMeta
from gui.Scaleform.locale.MENU import MENU

from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *
from xfw.events import registerEvent, overrideMethod


boostersName = dict.fromkeys(BTN.values())
clanReservesName = dict.fromkeys(BTN.values())
boosterEnabled = True

autoReloadConfig = False
isBattle = False
goodiesCache = dependency.instance(IGoodiesCache)

activeBoosters = None
activeReserves = {}
activeClanReserves = None

BOOSTER_ICON_EMPTY = 'img://gui/maps/icons/filters/empty.png'


class Reserve(object):

    def __init__(self, goodieDescription, finishTime):
        self.finishTime = finishTime
        self.goodieDescription = goodieDescription
        self.effectTime = goodieDescription.lifetime

    def getUsageLeftTime(self):
        return time_utils.getTimeDeltaFromNow(time_utils.makeLocalServerTime(self.finishTime)) if self.finishTime is not None else 0

    def getShortLeftTimeStr(self):
        return time_utils.getTillTimeString(self.getUsageLeftTime(), MENU.TIME_TIMEVALUESHORT)

    @property
    def boosterType(self):
        return self.goodieDescription.resource.resourceType

    @property
    def boosterGuiType(self):
        return BTN[self.boosterType]

    @property
    def userName(self):
        return _ms(MENU.boosterTypeLocale(self.boosterGuiType))


def readConfig():
    global autoReloadConfig, boostersName, boosterEnabled
    autoReloadConfig = config.get('autoReloadConfig')
    boosterEnabled = config.get('boosters/enabled', True)
    if boosterEnabled:
        for k in boostersName.iterkeys():
            boostersName[k] = config.get(
                'boosters/boostersName/{}'.format(k[8:]), None)
        for k in clanReservesName.iterkeys():
            clanReservesName[k] = config.get(
                'boosters/clanReservesName/{}'.format(k[8:]), None)


readConfig()


@overrideMethod(LobbyHeaderMeta, 'as_setBoosterDataS')
def as_setBoosterDataS(base, self, data):
    #log('data = %s' % data)
    if data['hasActiveBooster'] and boosterEnabled and config.get('boosters/hideActiveBooster', False):
        data['boosterIcon'] = BOOSTER_ICON_EMPTY
        data['boosterBg'] = BOOSTER_ICON_EMPTY
        data['boosterText'] = ''
    base(self, data)


@registerEvent(PlayerAccount, 'onArenaCreated')
def onArenaCreated(self):
    global isBattle
    isBattle = True


@registerEvent(Hangar, '_populate')
def Hangar_populate(self):
    global isBattle
    isBattle = False


def reserevOfIndex(index, reserves):
    countReserves = len(reserves)
    if countReserves == 0:
        return index, None
    if index == 0:
        listFinishTime = [x.finishTime for x in reserves]
        index = listFinishTime.index(min(listFinishTime)) + 1
    return index, (reserves[index - 1] if (index > 0) and (countReserves >= index) else None)


def booster(index):
    global activeBoosters
    if not isBattle:
        activeBoosters = []
        for boosterValues in goodiesCache.getBoosters(criteria=REQ_CRITERIA.BOOSTER.ACTIVE).itervalues():
            activeBoosters.append(Reserve(boosterValues._goodieDescription, boosterValues.finishTime))
    index, result = reserevOfIndex(index, activeBoosters)
    if isBattle:
        if (result is not None) and (result.getUsageLeftTime() <= 0):
            activeBoosters.pop(index-1)
            return None
    return result


def clanReserv(index):
    global activeClanReserves
    if not isBattle:
        activeClanReserves = goodiesCache.getClanReserves().values()
    index, result = reserevOfIndex(index, activeClanReserves)
    if isBattle:
        if (result is not None) and (result.getUsageLeftTime() <= 0):
            activeClanReserves.pop(index-1)
            return None
    return result


@xvm.export('bst.countBoosters', deterministic=False)
def getCountBoosters():
    global activeBoosters
    if not isBattle:
        activeBoosters = goodiesCache.getBoosters(
            criteria=REQ_CRITERIA.BOOSTER.ACTIVE).values()
    return len(activeBoosters)


@xvm.export('bst.leftTimeMin', deterministic=False)
def leftTimeMin(index=0, norm=None):
    b = booster(index)
    if b is not None:
        seconds = b.getUsageLeftTime()
        return norm * seconds / b.effectTime if isinstance(norm, (float, int)) else seconds / 60
    return None


@xvm.export('bst.leftTime', deterministic=False)
def leftTime(index=0):
    b = booster(index)
    return b.getShortLeftTimeStr() if b is not None else None


@xvm.export('bst.name', deterministic=False)
def leftTime(index=0):
    b = booster(index)
    if b is None:
        return None
    if autoReloadConfig:
        readConfig()
    if not boosterEnabled:
        return b.userName
    boosterName = boostersName.get(b.boosterGuiType, None)
    return b.userName if boosterName is None else boosterName


@xvm.export('bst.type', deterministic=False)
def bst_type(index=0):
    b = booster(index)
    return b.boosterGuiType if b is not None else None


@xvm.export('bst.countCR', deterministic=False)
def getCountBoosters():
    global activeClanReserves
    if not isBattle:
        activeClanReserves = goodiesCache.getClanReserves().values()
    return len(activeClanReserves)


@xvm.export('bst.leftTimeMinCR', deterministic=False)
def leftTimeMin(index=0, norm=None):
    b = clanReserv(index)
    if b is not None:
        seconds = b.getUsageLeftTime()
        return norm * seconds / b.effectTime if isinstance(norm, (float, int)) else seconds / 60
    return None


@xvm.export('bst.leftTimeCR', deterministic=False)
def leftTime(index=0):
    b = clanReserv(index)
    return time_utils.getTillTimeString(b.getUsageLeftTime(), MENU.TIME_TIMEVALUESHORT) if b is not None else None


@xvm.export('bst.nameCR', deterministic=False)
def leftTime(index=0):
    b = clanReserv(index)
    if b is None:
        return None
    if autoReloadConfig:
        readConfig()
    if not boosterEnabled:
        return b.userName
    clanReserveName = clanReservesName.get(b.boosterGuiType, None)
    return b.userName if clanReserveName is None else clanReserveName


@xvm.export('bst.typeCR', deterministic=False)
def bst_type(index=0):
    b = clanReserv(index)
    return b.boosterGuiType if b is not None else None
