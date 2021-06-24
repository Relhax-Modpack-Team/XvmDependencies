import BigWorld
from Avatar import PlayerAvatar
from constants import ARENA_GUI_TYPE, VEHICLE_CLASSES
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.battle_control.arena_info.arena_dp import ArenaDataProvider
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

import xvm_main.python.config as config
from xfw.events import registerEvent
from xfw_actionscript.python import *
from xvm_main.python.logger import *
from xvm_main.python.stats import _stat

from xvm.damageLog import RATINGS
from xvm.parser_addon import parser_addon

playersEnemyAlive = {}
playersAllyAlive = {}
playersEnemyDead = {}
playersAllyDead = {}
aliveVehType = {'LT': '', 'MT': '', 'HT': '', 'SPG': '', 'TD': '', 'unknown': ''}
deadVehType = {'LT': '', 'MT': '', 'HT': '', 'SPG': '', 'TD': '', 'unknown': ''}
enemyVehicleAlive = None
allyVehicleAlive = None
enemyVehicleDead = None
allyVehicleDead = None
playerTeam = 0
autoReloadConfig = False
twoLine = False
countAlly = 0
countEnemy = 0
arenaGuiType = None
allyOrder = []
enemyOrder = []
chooseRating = None
directSortByLevelAllys = True
directSortByLevelEnemies = True
waitCallback = False


def readConfig():
    global aliveVehType, deadVehType, twoLine, enemyOrder, allyOrder, arenaGuiType, autoReloadConfig, chooseRating, directSortByLevelEnemies, directSortByLevelAllys
    scale = config.networkServicesSettings.scale
    name = config.networkServicesSettings.rating
    r = '{}_{}'.format(scale, name)
    if r in RATINGS:
        chooseRating = RATINGS[r]['name']
    else:
        chooseRating = 'xwgr' if scale == 'xvm' else 'wgr'
    autoReloadConfig = config.get('autoReloadConfig')
    aliveVehType['LT'] = config.get('fragCorrelation/vtypeAlive/LT', "<font face='xvm' color='#238C23'>&#x3A;</font>")
    aliveVehType['MT'] = config.get('fragCorrelation/vtypeAlive/MT', "<font face='xvm' color='#B79B2D'>&#x3B;</font>")
    aliveVehType['HT'] = config.get('fragCorrelation/vtypeAlive/HT', "<font face='xvm' color='#AA2F31'>&#x3F; </font>")
    aliveVehType['SPG'] = config.get('fragCorrelation/vtypeAlive/SPG', "<font face='xvm' color='#7D04A0'>&#x2D;</font>")
    aliveVehType['TD'] = config.get('fragCorrelation/vtypeAlive/TD', "<font face='xvm' color='#1447A0'>&#x2E;</font>")
    aliveVehType['unknown'] = config.get('fragCorrelation/vtypeAlive/unknown', "<font face='xvm' color='#dfdfd0'>&#x44;</font>")
    deadVehType['LT'] = config.get('fragCorrelation/vtypeDead/LT', "<font face='xvm' color='#387638'>&#x3A;</font>")
    deadVehType['MT'] = config.get('fragCorrelation/vtypeDead/MT', "<font face='xvm' color='#9c9c36'>&#x3B;</font>")
    deadVehType['HT'] = config.get('fragCorrelation/vtypeDead/HT', "<font face='xvm' color='#803c3c'>&#x3F; </font>")
    deadVehType['SPG'] = config.get('fragCorrelation/vtypeDead/SPG', "<font face='xvm' color='#854994'>&#x2D;</font>")
    deadVehType['TD'] = config.get('fragCorrelation/vtypeDead/TD', "<font face='xvm' color='#465a97'>&#x2E;</font>")
    deadVehType['unknown'] = config.get('fragCorrelation/vtypeDead/unknown', "<font face='xvm' color='#dfdfd0'>&#x44;</font>")
    showStandartMarkers = config.get('fragCorrelation/showStandartMarkers', False)
    enemyOrder = config.get('fragCorrelation/markersEnemiesOrder', ['HT', 'MT', 'TD', 'SPG', 'LT', 'unknown'])
    allyOrder = config.get('fragCorrelation/markersAllysOrder', ['HT', 'MT', 'TD', 'SPG', 'LT', 'unknown'])
    directSortByLevelAllys = config.get('fragCorrelation/directSortByLevelAllys', True)
    directSortByLevelEnemies = config.get('fragCorrelation/directSortByLevelEnemies', True)
    if not showStandartMarkers:
        settingsCore = dependency.instance(ISettingsCore)
        if settingsCore.isSettingChanged('showVehiclesCounter', False):
            settingsCore.applySetting('showVehiclesCounter', False)
            settingsCore.onSettingsChanged({'showVehiclesCounter': False})
    arenaGuiType = BigWorld.player().arenaGuiType
    if arenaGuiType in [ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING]:
        twoLine = config.get('fragCorrelation/twoLineEpicRandom', False)
    else:
        twoLine = False


def getAliveVehicle(vehicles, countHalf, isAlly=True):
    if isAlly:
        sign = -1 if directSortByLevelAllys else 1
        vehicles.sort(key=lambda x: [x['vehTypeNumber'], sign * x['level']])
    else:
        sign = -1 if directSortByLevelEnemies else 1
        vehicles.sort(key=lambda x: [x['vehTypeNumber'], sign * x['level']])
    s = [parser_addon(aliveVehType[i['vehType']], i) for i in vehicles]
    if twoLine and (len(s) >= countHalf):
        s.insert(countHalf, '\n')
    return ''.join(s) if s is not None else ''


def getDeadVehicle(vehicles, countHalf, isAlly=True):
    if isAlly:
        sign = -1 if directSortByLevelAllys else 1
        vehicles.sort(key=lambda x: [x['vehTypeNumber'], sign * x['level']])
    else:
        sign = -1 if directSortByLevelEnemies else 1
        vehicles.sort(key=lambda x: [x['vehTypeNumber'], sign * x['level']])
    s = [parser_addon(deadVehType[i['vehType']], i) for i in vehicles]
    l = len(s) - countHalf
    if twoLine and (l > 0):
        s.insert(l, '\n')
    return ''.join(s) if s is not None else ''


def readColor(sec, m, xm=None):
    colors = config.get('colors/' + sec)
    if m is not None and colors is not None:
        for val in colors:
            if val['value'] > m:
                return '#' + val['color'][2:] if val['color'][:2] == '0x' else val['color']
    elif xm is not None:
        colors_x = config.get('colors/x')
        for val in colors_x:
            if val['value'] > xm:
                return '#' + val['color'][2:] if val['color'][:2] == '0x' else val['color']


def getStats(name):
    if (_stat.resp is not None) and ('players' in _stat.resp) and (name in _stat.resp['players']):
        stats = _stat.resp['players'][name]
        xwn8 = stats.get('xwn8', None)
        xwtr = stats.get('xwtr', None)
        xeff = stats.get('xeff', None)
        xwgr = stats.get('xwgr', None)
        return {'c:wn8': readColor('wn8', stats.get('wn8', None), xwn8),
                'c:xwn8': readColor('x', xwn8),
                'c:wtr': readColor('wtr', stats.get('wtr', None), xwtr),
                'c:xwtr': readColor('x', xwtr),
                'c:eff': readColor('eff', stats.get('eff', None), xeff),
                'c:xeff': readColor('x', xeff),
                'c:wgr': readColor('wgr', stats.get('wgr', None), xwgr),
                'c:xwgr': readColor('x', xwgr),
                'c:xte': readColor('x', stats.get('v').get('xte', None))}
    else:
        return {'c:wn8': None, 'c:xwn8': None, 'c:wtr': None, 'c:xwtr': None, 'c:eff': None, 'c:xeff': None, 'c:wgr': None, 'c:xwgr': None, 'c:xte': None}


def _event():
    if waitCallback:
        as_event('ON_UPDATE_FRAG_COR_BAR')


def update(vInfoVO):
    global playersEnemyAlive, playersAllyAlive, playersEnemyDead, playersAllyDead, countAlly, countEnemy, playerTeam
    global enemyVehicleAlive, allyVehicleAlive, enemyVehicleDead, allyVehicleDead
    # start_t = time.clock()
    if not (enemyOrder and allyOrder) or autoReloadConfig:
        readConfig()
    renameDict = {'lightTank': 'LT', 'mediumTank': 'MT', 'heavyTank': 'HT', 'SPG': 'SPG', 'AT-SPG': 'TD', None: 'unknown'}

    if playerTeam < 1:
        avatar = BigWorld.player()
        if hasattr(avatar, 'team'):
            playerTeam = avatar.team
        else:
            return

    if isinstance(vInfoVO, dict):
        _vehicleID = vInfoVO.get('vID', 0)
        _vehicleType = vInfoVO['vehicleType'].type
        classTag = list(_vehicleType.tags.intersection(VEHICLE_CLASSES))[0]
        name = vInfoVO.get('name', None)
        isAlly = 'ally' if playerTeam == vInfoVO.get('team', -1) else None
        isAlive = bool(vInfoVO.get('isAlive', 1))
    else:
        _vehicleID = vInfoVO.vehicleID
        _vehicleType = vInfoVO.vehicleType
        classTag = _vehicleType.classTag
        name = vInfoVO.player.name
        isAlly = 'ally' if playerTeam == vInfoVO.team else None
        isAlive = vInfoVO.isAlive()
    vehInfo = {'vehType': renameDict[classTag],
               'level': _vehicleType.level,
               'c:r': '{{c:%s}}' % chooseRating,
               'playerName': name,
               'ally': isAlly}

    isNewPlayerAlive = (_vehicleID in playersAllyAlive) or (_vehicleID in playersEnemyAlive)
    isNewPlayerDead = (_vehicleID in playersAllyDead) or (_vehicleID in playersEnemyDead)
    if isAlive and not isNewPlayerAlive:
        if isAlly is not None:
            vehInfo['vehTypeNumber'] = allyOrder.index(vehInfo['vehType'])
            playersAllyAlive[_vehicleID] = vehInfo
            countAlly += 1
            allyVehicleAlive = getAliveVehicle(playersAllyAlive.values(), countAlly >> 1)
        else:
            vehInfo['vehTypeNumber'] = enemyOrder.index(vehInfo['vehType'])
            playersEnemyAlive[_vehicleID] = vehInfo
            countEnemy += 1
            enemyVehicleAlive = getAliveVehicle(playersEnemyAlive.values(), countEnemy >> 1, False)
        _event()
    elif (not isAlive) and not isNewPlayerDead:
        if isAlly is not None:
            if _vehicleID in playersAllyAlive:
                playersAllyDead[_vehicleID] = playersAllyAlive[_vehicleID]
                del playersAllyAlive[_vehicleID]
                allyVehicleAlive = getAliveVehicle(playersAllyAlive.values(), countAlly >> 1)
            else:
                vehInfo['vehTypeNumber'] = allyOrder.index(vehInfo['vehType'])
                playersAllyDead[_vehicleID] = vehInfo
            allyVehicleDead = getDeadVehicle(playersAllyDead.values(), countAlly >> 1)
        else:
            if _vehicleID in playersEnemyAlive:
                playersEnemyDead[_vehicleID] = playersEnemyAlive[_vehicleID]
                del playersEnemyAlive[_vehicleID]
                enemyVehicleAlive = getAliveVehicle(playersEnemyAlive.values(), countEnemy >> 1, False)
            else:
                vehInfo['vehTypeNumber'] = enemyOrder.index(vehInfo['vehType'])
                playersEnemyDead[_vehicleID] = vehInfo
            enemyVehicleDead = getDeadVehicle(playersEnemyDead.values(), countEnemy >> 1, False)
        _event()
    elif (classTag is not None) and isNewPlayerAlive:
        if (_vehicleID in playersAllyAlive) and (playersAllyAlive[_vehicleID]['vehType'] == 'unknown'):
            vehInfo['vehTypeNumber'] = allyOrder.index(vehInfo['vehType'])
            playersAllyAlive[_vehicleID] = vehInfo
            allyVehicleAlive = getAliveVehicle(playersAllyAlive.values(), countAlly >> 1)
            _event()
        elif (_vehicleID in playersEnemyAlive) and (playersEnemyAlive[_vehicleID]['vehType'] == 'unknown'):
            vehInfo['vehTypeNumber'] = enemyOrder.index(vehInfo['vehType'])
            playersEnemyAlive[_vehicleID] = vehInfo
            enemyVehicleAlive = getAliveVehicle(playersEnemyAlive.values(), countEnemy >> 1, False)
            _event()


def getStat():
    global playersEnemyAlive, playersAllyAlive, playersEnemyDead, playersAllyDead
    global enemyVehicleAlive, allyVehicleAlive, enemyVehicleDead, allyVehicleDead
    for k, v in playersEnemyAlive.iteritems():
        playersEnemyAlive[k].update(getStats(v['playerName']))
    for k, v in playersAllyAlive.iteritems():
        playersAllyAlive[k].update(getStats(v['playerName']))
    for k, v in playersEnemyDead.iteritems():
        playersEnemyDead[k].update(getStats(v['playerName']))
    for k, v in playersAllyDead.iteritems():
        playersAllyDead[k].update(getStats(v['playerName']))
    allyVehicleAlive = getAliveVehicle(playersAllyAlive.values(), countAlly >> 1)
    enemyVehicleAlive = getAliveVehicle(playersEnemyAlive.values(), countEnemy >> 1, False)
    allyVehicleDead = getDeadVehicle(playersAllyDead.values(), countAlly >> 1)
    enemyVehicleDead = getDeadVehicle(playersEnemyDead.values(), countEnemy >> 1, False)
    as_event('ON_UPDATE_FRAG_COR_BAR')


@registerEvent(_stat, '_get_battle')
def _get_battle():
    BigWorld.callback(0, getStat)


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    update(vInfoVO)


@registerEvent(ArenaDataProvider, '_ArenaDataProvider__addVehicleInfoVO')
def __addVehicleInfoVO(self, vID, vInfoVO):
    update(vInfoVO)


@registerEvent(ArenaDataProvider, 'updateVehicleInfo')
def updateVehicleInfo(self, vID, vInfo):
    vInfo['vID'] = vID
    update(vInfo)


@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    global playersEnemyAlive, playersAllyAlive, playersEnemyDead, playersAllyDead, countAlly, countEnemy, aliveVehType, deadVehType, arenaGuiType
    global enemyOrder, allyOrder, enemyVehicleAlive, allyVehicleAlive, enemyVehicleDead, allyVehicleDead, playerTeam, chooseRating, waitCallback
    countAlly = 0
    countEnemy = 0
    playerTeam = 0
    arenaGuiType = None
    allyOrder = []
    enemyOrder = []
    playersEnemyAlive = {}
    playersAllyAlive = {}
    playersEnemyDead = {}
    playersAllyDead = {}
    enemyVehicleAlive = None
    allyVehicleAlive = None
    enemyVehicleDead = None
    allyVehicleDead = None
    chooseRating = None
    waitCallback = False
    aliveVehType = {'LT': '', 'MT': '', 'HT': '', 'SPG': '', 'TD': ''}
    deadVehType = {'LT': '', 'MT': '', 'HT': '', 'SPG': '', 'TD': ''}


@registerEvent(PlayerAvatar, 'onEnterWorld')
def onEnterWorld(self, prereqs):
    global waitCallback
    waitCallback = True
    as_event('ON_UPDATE_FRAG_COR_BAR')


@xvm.export('fcb.enemyVehicleAlive', deterministic=False)
def fcb_enemyVehicleAlive():
    return enemyVehicleAlive


@xvm.export('fcb.allyVehicleAlive', deterministic=False)
def fcb_allyVehicleAlive():
    return allyVehicleAlive


@xvm.export('fcb.enemyVehicleDead', deterministic=False)
def fcb_enemyVehicleDead():
    return enemyVehicleDead


@xvm.export('fcb.allyVehicleDead', deterministic=False)
def fcb_allyVehicleDead():
    return allyVehicleDead


@xvm.export('fcb.countEnemyAlive', deterministic=False)
def fcb_countEnemyAlive(veh):
    if isinstance(veh, basestring) and (veh.upper() in ['HT', 'MT', 'TD', 'SPG', 'LT']):
        return len([True for v in playersEnemyAlive.itervalues() if v['vehType'] == veh])
    else:
        return None


@xvm.export('fcb.countAllyAlive', deterministic=False)
def fcb_countAllyAlive(veh):
    if isinstance(veh, basestring) and (veh.upper() in ['HT', 'MT', 'TD', 'SPG', 'LT']):
        return len([True for v in playersAllyAlive.itervalues() if v['vehType'] == veh])
    else:
        return None


@xvm.export('fcb.countEnemyDead', deterministic=False)
def fcb_countEnemyDead(veh):
    if isinstance(veh, basestring) and (veh.upper() in ['HT', 'MT', 'TD', 'SPG', 'LT']):
        return len([True for v in playersEnemyDead.itervalues() if v['vehType'] == veh])
    else:
        return None


@xvm.export('fcb.countAllyDead', deterministic=False)
def fcb_countAllyDead(veh):
    if isinstance(veh, basestring) and (veh.upper() in ['HT', 'MT', 'TD', 'SPG', 'LT']):
        return len([True for v in playersAllyDead.itervalues() if v['vehType'] == veh])
    else:
        return None


@xvm.export('fcb.aliveVehType', deterministic=False)
def fcb_aliveVehType(veh):
    if isinstance(veh, basestring) and (veh.upper() in ['HT', 'MT', 'TD', 'SPG', 'LT']):
        return aliveVehType[veh]
    else:
        return None


@xvm.export('fcb.deadVehType', deterministic=False)
def fcb_deadVehType(veh):
    if isinstance(veh, basestring) and (veh.upper() in ['HT', 'MT', 'TD', 'SPG', 'LT']):
        return deadVehType[veh]
    else:
        return None
