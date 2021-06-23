import BigWorld
import game
import nations
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES as BET
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
import xvm_main.python.userprefs as userprefs
from xfw.events import registerEvent
from xfw_actionscript.python import *
from xvm_main.python.logger import *
from xvm_main.python.stats import _stat

import parser_addon
from xvm.damageLog import VEHICLE_CLASSES, keyLower, RATINGS

macros = None
autoReloadConfig = None
hitLogConfig = {}
isDownAlt = False
isEpicBattle = False
chooseRating = None

ASSIST_TRACK = BET.ASSIST_TRACK
ASSIST_SPOT = BET.ASSIST_SPOT
STUN = BET.ASSIST_STUN
ALL_ASSIST = [ASSIST_TRACK, ASSIST_SPOT, STUN]

#-----------------------
C_ASSIST_TYPE = {"stun": "#CCCCCC",
                 "assistTrack": "#CCCCCC",
                 "assistSpot":   "#CCCCCC"}
ASSIST_TYPE = {"stun": "<font face='xvm'>&#x117;</font>",
               "assistTrack": "<font face='xvm'>&#x116;</font>",
               "assistSpot": "<font face='xvm'>&#x10A;</font>"}
VTYPE = {"mediumTank": "<font face='xvm'>&#x3B;</font>",
         "lightTank": "<font face='xvm'>&#x3A;</font>",
         "heavyTank": "<font face='xvm'>&#x3F;</font>",
         "AT-SPG": "<font face='xvm'>&#x2E;</font>",
         "SPG": "<font face='xvm'>&#x2D;</font>",
         "not_vehicle": ""
        }
C_VTYPE = {"mediumTank": "#FFF198",
           "lightTank": "#A2FF9A",
           "heavyTank": "#FFACAC",
           "AT-SPG": "#A0CFFF",
           "SPG": "#EFAEFF",
           "not_vehicle": "#CCCCCC"
           }
HOTKEYS = {"enabled": True, "keyCode": 56, "onHold": True}
#-----------------------

ASSIST_LOG = 'assistLog/'
FORMAT_HISTORY = 'formatHistory'
GROUP_HITS_PLAYER = 'groupHitsByPlayer'
ADD_TO_END = 'addToEnd'
LINES = 'lines'
MOVE_IN_BATTLE = 'moveInBattle'
ENABLED = ASSIST_LOG + 'enabled'
SHOW_SELF_DAMAGE = ASSIST_LOG + 'showSelfDamage'
SHOW_ALLY_DAMAGE = ASSIST_LOG + 'showAllyDamage'
DEFAULT_X = 320
DEFAULT_Y = 0

SECTION_LOG = ASSIST_LOG + 'log/'
SECTION_ALT_LOG = ASSIST_LOG + 'altLog/'
SECTION_BACKGROUND = ASSIST_LOG + 'backgroundLog/'
SECTION_ALT_BACKGROUND = ASSIST_LOG + 'altBackgroundLog/'
SECTIONS = (SECTION_LOG, SECTION_ALT_LOG, SECTION_BACKGROUND, SECTION_ALT_BACKGROUND)

APPEND = 0
INSERT = 1
CHANGE = 2


def readyConfig(section):
    if autoReloadConfig or (section not in hitLogConfig):
        return {'vtype': keyLower(config.get(section + 'vtype', VTYPE)),
                'c:vtype': keyLower(config.get(section + 'c:vtype', C_VTYPE)),
                'c:assist-type': keyLower(config.get(section + 'c:assist-type', C_ASSIST_TYPE)),
                'assist-type': keyLower(config.get(section + 'assist-type', ASSIST_TYPE)),
                }
    else:
        return hitLogConfig[section]


def updateValueMacros(section, value):
    global macros

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

    conf = readyConfig(section)
    if macros is None:
        xwn8 = value.get('xwn8', None)
        xwtr = value.get('xwtr', None)
        xeff = value.get('xeff', None)
        xwgr = value.get('xwgr', None)
        macros = {'vehicle': value['shortUserString'],
                  'name': value['name'],
                  'clannb': value['clanAbbrev'],
                  'clan': ''.join(['[', value['clanAbbrev'], ']']) if value['clanAbbrev'] else '',
                  'level': value['level'],
                  'clanicon': value['clanicon'],
                  'squad-num': value['squadnum'],
                  'wn8': value.get('wn8', None),
                  'xwn8': value.get('xwn8', None),
                  'wtr': value.get('wtr', None),
                  'xwtr': value.get('xwtr', None),
                  'eff': value.get('eff', None),
                  'xeff': value.get('xeff', None),
                  'wgr': value.get('wgr', None),
                  'xwgr': value.get('xwgr', None),
                  'xte': value.get('xte', None),
                  'r': '{{%s}}' % chooseRating,
                  'xr': '{{%s}}' % chooseRating if chooseRating[0] == 'x' else '{{x%s}}' % chooseRating,
                  'c:r': '{{c:%s}}' % chooseRating,
                  'c:xr': '{{c:%s}}' % chooseRating if chooseRating[0] == 'x' else '{{c:x%s}}' % chooseRating,
                  'c:wn8': readColor('wn8', value.get('wn8', None), xwn8),
                  'c:xwn8': readColor('x', xwn8),
                  'c:wtr': readColor('wtr', value.get('wtr', None), xwtr),
                  'c:xwtr': readColor('x', xwtr),
                  'c:eff': readColor('eff', value.get('eff', None), xeff),
                  'c:xeff': readColor('x', xeff),
                  'c:wgr': readColor('wgr', value.get('wgr', None), xwgr),
                  'c:xwgr': readColor('x', xwgr),
                  'c:xte': readColor('x', value.get('xte', None)),
                  'nation': value.get('nation', None),
                  'assist': value['assist'],
                  'track': value['assistTrack'],
                  'spot': value['assistSpot'],
                  'stun': value['assistStun'],
                  'sum-assist': value['sumAssist'],
                  'sum-track': value['sumAssistTrack'],
                  'sum-spot': value['sumAssistSpot'],
                  'sum-stun': value['sumAssistStun'],
                  'assist-ratio': value['assistRatio'],
                  'sum-assist-ratio': value['sumAssistRatio'],
                  'track-ratio': value['assistTrackRatio'],
                  'sum-track-ratio': value['sumAssistTrackRatio'],
                  'spot-ratio': value['assistSpotRatio'],
                  'sum-spot-ratio': value['sumAssistSpotRatio'],
                  'stun-ratio': value['assistStunRatio'],
                  'sum-stun-ratio': value['sumAssistStunRatio'],
                  'count': value['count'],
                  'count-track': value['countTrack'],
                  'count-spot': value['countSpot'],
                  'count-stun': value['countStun'],
                  'sum-count': value['sumCount'],
                  'total-count': value['totalCount'],
                  'alive': 'al' if value['isAlive'] else None,
                  'stun': 'st' if value['hasStun'] else None,
                  # 'assist-type': value['assistType'],
                  'c:assist': readColor('dmg_ratio_player', value.get('assistRatio', None)),
                  'c:sum-assist': readColor('dmg_ratio_player', value.get('sumAssistRatio', None)),
                  'c:track': readColor('dmg_ratio_player', value.get('assistTrackRatio', None)),
                  'c:sum-track': readColor('dmg_ratio_player', value.get('sumAssistTrackRatio', None)),
                  'c:spot': readColor('dmg_ratio_player', value.get('assistSpotRatio', None)),
                  'c:sum-spot': readColor('dmg_ratio_player', value.get('sumAssistSpotRatio', None)),
                  'c:stun': readColor('dmg_ratio_player', value.get('assistStunRatio', None)),
                  'c:sum-stun': readColor('dmg_ratio_player', value.get('sumAssistStunRatio', None))
                  }
    macros.update({'c:assist-type': conf['c:assist-type'].get(value['assistType'].lower(), '#FFFFFF'),
                   'assist-type': conf['assist-type'].get(value['assistType'].lower(), ''),
                   'vtype': conf['vtype'][value['attackedVehicleType']],
                   'c:vtype': conf['c:vtype'][value['attackedVehicleType']]
                   # 'splash-hit': conf['splashHit'].get(value['splashHit'], 'unknown'),
                   # 'critical-hit': conf['criticalHit'].get('critical') if value['criticalHit'] else conf['criticalHit'].get('no-critical'),
                   # 'c:hit-effects': conf['c_hitEffect'].get(value['hitEffect'], 'unknown'),
                   # 'hit-effects': conf['hitEffect'].get(value['hitEffect'], 'unknown'),
                   # 'crit-device': conf['critDevice'].get(value.get('critDevice', '')),
                   # 'number': value['number'],
                   })


def parser(strHTML):
    s = parser_addon.parser_addon(strHTML, macros)
    return s


class DataAssistLog(object):
    guiSessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.player = None
        self.reset()

    def reset(self):
        self.vehicles = {}
        self.vehId = None
        self.ribbonType = None
        self.totalCount = 0
        self.data = {'assist': 0,
                     'assistTrack': 0,
                     'assistSpot': 0,
                     'assistStun': 0,
                     'sumAssist': 0,
                     'sumAssistTrack': 0,
                     'sumAssistSpot': 0,
                     'sumAssistStun': 0,
                     # 'totalDamage': 0,
                     'assistRatio': 0,
                     'sumAssistRatio': 0,
                     'assistTrackRatio': 0,
                     'sumAssistTrackRatio': 0,
                     'assistSpotRatio': 0,
                     'sumAssistSpotRatio': 0,
                     'assistStunRatio': 0,
                     'sumAssistStunRatio': 0,
                     'count': 0,
                     'countTrack': 0,
                     'countSpot': 0,
                     'countStun': 0,
                     'sumCount': 0,
                     'totalCount': 0,
                     'vehicleID': None,
                     'isAlive': True,
                     'attackedVehicleType': None,
                     'shortUserString': None,
                     'level': None,
                     'nation': None,
                     'name': None,
                     'clanAbbrev': None,
                     'clanicon': None,
                     'squadnum': None,
                     'hasStun': False
                     }

    def updateLabels(self):
        # start_t = time.clock()
        global macros
        macros = None
        _log.callEvent = _backgroundLog.callEvent = not isDownAlt
        _altLog.callEvent = _altBackgroundLog.callEvent = isDownAlt
        _altLog.output()
        _log.output()
        # start_t = time.clock()
        # log('updateLabels')
        # global prof_time
        # prof_time += time.clock() - start_t
        # log('time_func = %.6f         |        total_time = %.6f' % (time.clock() - start_t, prof_time))
        _backgroundLog.output()
        _altBackgroundLog.output()

    def updateData(self):
        # player = BigWorld.player()
        vehicleID = self.vehId
        self.data['vehicleID'] = vehicleID
        self.data['assistType'] = self.ribbonType
        curVehicle = self.vehicles[vehicleID]
        pl = _stat.players.get(vehicleID, None)
        self.data['assist'] = curVehicle[self.ribbonType]['value']
        # self.data['sumAssist'] = curVehicle[self.ribbonType]['sum']
        # for assistType in curVehicle:
        #     log('assistType = %s' % assistType)
        listDamage = [assistType.get('sum', 0) for assistType in curVehicle.itervalues()]
        self.data['sumAssist'] = reduce(lambda x, y: x + y, listDamage, 0)
        self.data['count'] = curVehicle[self.ribbonType]['count']
        listCount = [assistType.get('count', 0) for assistType in curVehicle.itervalues()]
        self.data['sumCount'] = reduce(lambda x, y: x + y, listCount, 0)
        self.data['totalCount'] += self.data['sumCount']
        # pl = ('vehicleID', 'accountDBID', 'name', 'clan', 'clanInfo', 'badgeId', 'team', 'vehCD', 'vLevel', 'maxHealth', 'vIcon', 'vn', 'vType', 'alive', 'ready', 'x_emblem', 'x_emblem_loading', 'clanicon')

        if pl is not None:
            self.data['assistRatio'] = self.data['assist'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
            self.data['sumAssistRatio'] = self.data['sumAssist'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
        else:
            self.data['assistRatio'] = 0
            self.data['sumAssistRatio'] = 0

        if ASSIST_TRACK in curVehicle:
            self.data['assistTrack'] = curVehicle[ASSIST_TRACK]['value']
            self.data['sumAssistTrack'] = curVehicle[ASSIST_TRACK]['sum']
            self.data['countTrack'] = curVehicle[ASSIST_TRACK]['count']
            if pl is not None:
                self.data['assistTrackRatio'] = self.data['assistTrack'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
                self.data['sumAssistTrackRatio'] = self.data['sumAssistTrack'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
            else:
                self.data['assistTrackRatio'] = 0
                self.data['sumAssistTrackRatio'] = 0
        else:
            self.data['assistTrack'] = 0
            self.data['sumAssistTrack'] = 0
            self.data['countTrack'] = 0
            self.data['assistTrackRatio'] = 0
            self.data['sumAssistTrackRatio'] = 0

        if ASSIST_SPOT in curVehicle:
            self.data['assistSpot'] = curVehicle[ASSIST_SPOT]['value']
            self.data['sumAssistSpot'] = curVehicle[ASSIST_SPOT]['sum']
            self.data['countSpot'] = curVehicle[ASSIST_SPOT]['count']
            if pl is not None:
                self.data['assistSpotRatio'] = self.data['assistSpot'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
                self.data['sumAssistSpotRatio'] = self.data['sumAssistSpot'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
            else:
                self.data['assistSpotRatio'] = 0
                self.data['sumAssistSpotRatio'] = 0
        else:
            self.data['assistSpot'] = 0
            self.data['sumAssistSpot'] = 0
            self.data['countSpot'] = 0
            self.data['assistSpotRatio'] = 0
            self.data['sumAssistSpotRatio'] = 0

        if STUN in curVehicle:
            self.data['assistStun'] = curVehicle[STUN]['value']
            self.data['sumAssistStun'] = curVehicle[STUN]['sum']
            self.data['countStun'] = curVehicle[STUN]['count']
            if pl is not None:
                self.data['assistStunRatio'] = self.data['assistStun'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
                self.data['sumAssistStunRatio'] = self.data['sumAssistStun'] * 100 // pl.maxHealth if pl.maxHealth > 0 else 0
            else:
                self.data['assistStunRatio'] = 0
                self.data['sumAssistStunRatio'] = 0
        else:
            self.data['assistStun'] = 0
            self.data['sumAssistStun'] = 0
            self.data['countStun'] = 0
            self.data['assistStunRatio'] = 0
            self.data['sumAssistStunRatio'] = 0

        if vehicleID:
            # entity = BigWorld.entity(vehicleID)
            # self.data['marksOnGun'] = '_' + str(entity.publicInfo['marksOnGun']) if (entity is not None) else None
            attacked = self.player.arena.vehicles.get(vehicleID)
            # attacked = {'forbidInBattleInvitations': False, 'vehicleType': <items.vehicles.VehicleDescriptor object at 0x2F88D430>, 'isAlive': True, 'name': 'DeFo1', 'igrType': 0, 'prebattleID': 0, 'potapovQuestIDs': [], 'accountDBID': 1356443, 'isPrebattleCreator': False, 'clanAbbrev': 'M3X1C', 'ranked': ((0, 0), []), 'isAvatarReady': True, 'team': 2, 'clanDBID': 222563, 'events': {}, 'isTeamKiller': False, 'crewGroup': 0}
            if attacked is not None:
                vehicleType = attacked['vehicleType']
                self.data['isAlive'] = attacked['isAlive']
                # vehicleType = ['_VehicleDescriptor__activeGunShotIdx', '_VehicleDescriptor__activeTurretPos', '_VehicleDescriptor__computeWeight', '_VehicleDescriptor__getChassisEffectNames', '_VehicleDescriptor__getIsHullAimingAvailable', '_VehicleDescriptor__get_boundingRadius', '_VehicleDescriptor__haveIncompatibleOptionalDevices', '_VehicleDescriptor__hornID', '_VehicleDescriptor__initFromCompactDescr', '_VehicleDescriptor__installGun', '_VehicleDescriptor__selectBestHull', '_VehicleDescriptor__selectTurretForGun', '_VehicleDescriptor__setHullAndCall', '_VehicleDescriptor__set_activeGunShotIndex', '_VehicleDescriptor__set_activeTurretPos', '_VehicleDescriptor__set_hornID', '_VehicleDescriptor__updateAttributes', 'activeGunShotIndex', 'activeTurretPosition', 'boundingRadius', 'camouflages', 'chassis', 'computeBaseInvisibility', 'engine', 'extras', 'extrasDict', 'fuelTank', 'getComponentsByType', 'getCost', 'getDevices', 'getHitTesters', 'getMaxRepairCost', 'gun', 'hasSiegeMode', 'hornID', 'hull', 'installComponent', 'installOptionalDevice', 'installTurret', 'isHullAimingAvailable', 'isPitchHullAimingAvailable', 'isYawHullAimingAvailable', 'keepPrereqs', 'level', 'makeCompactDescr', 'maxHealth', 'mayInstallComponent', 'mayInstallOptionalDevice', 'mayInstallTurret', 'mayRemoveOptionalDevice', 'miscAttrs', 'name', 'onSiegeStateChanged', 'optionalDevices', 'physics', 'playerEmblems', 'playerInscriptions', 'prerequisites', 'radio', 'removeOptionalDevice', 'setCamouflage', 'setPlayerEmblem', 'setPlayerInscription', 'shot', 'turret', 'turrets', 'type']
                if vehicleType:
                    _type = vehicleType.type
                    self.data['attackedVehicleType'] = list(_type.tags.intersection(VEHICLE_CLASSES))[0].lower()
                    self.data['shortUserString'] = _type.shortUserString
                    self.data['level'] = vehicleType.level
                    self.data['nation'] = nations.NAMES[_type.customizationNationID]
                else:
                    self.data['attackedVehicleType'] = None
                    self.data['shortUserString'] = None
                    self.data['level'] = None
                    self.data['nation'] = None
                self.data['name'] = attacked['name']
                if (_stat.resp is not None) and (attacked['name'] in _stat.resp['players']):
                    stats = _stat.resp['players'][attacked['name']]
                    self.data['wn8'] = stats.get('wn8', None)
                    self.data['xwn8'] = stats.get('xwn8', None)
                    self.data['wtr'] = stats.get('wtr', None)
                    self.data['xwtr'] = stats.get('xwtr', None)
                    self.data['eff'] = stats.get('e', None)
                    self.data['xeff'] = stats.get('xeff', None)
                    self.data['wgr'] = stats.get('wgr', None)
                    self.data['xwgr'] = stats.get('xwgr', None)
                    self.data['xte'] = stats.get('v').get('xte', None)
                else:
                    self.data['wn8'] = None
                    self.data['xwn8'] = None
                    self.data['wtr'] = None
                    self.data['xwtr'] = None
                    self.data['eff'] = None
                    self.data['xeff'] = None
                    self.data['wgr'] = None
                    self.data['xwgr'] = None
                    self.data['xte'] = None
                self.data['clanAbbrev'] = attacked['clanAbbrev']
            else:
                self.data['isAlive'] = False
            self.data['clanicon'] = _stat.getClanIcon(vehicleID)

            arenaDP = self.guiSessionProvider.getArenaDP()
            if arenaDP is not None:
                vInfo = arenaDP.getVehicleInfo(vID=vehicleID)
                self.data['squadnum'] = vInfo.squadIndex if vInfo.squadIndex != 0 else None
            else:
                self.data['squadnum'] = None
        else:
            self.data['attackedVehicleType'] = 'not_vehicle'
            self.data['shortUserString'] = ''
            self.data['name'] = ''
            self.data['clanAbbrev'] = ''
            self.data['level'] = None
            self.data['clanicon'] = None
            self.data['squadnum'] = None
        self.updateLabels()

    def isPlayerVehicle(self):
        if self.player is not None:
            if hasattr(self.player.inputHandler.ctrl, 'curVehicleID'):
                vId = self.player.inputHandler.ctrl.curVehicleID
                v = vId.id if isinstance(vId, Vehicle) else vId
                return self.player.playerVehicleID == v
            else:
                return True
        else:
            return False

    def onAppearanceReady(self, vehicle):
        self.player = BigWorld.player()
        self.data['hasStun'] = vehicle.typeDescriptor.shot.shell.hasStun

    def ribbonUpdated(self, ribbon):
        if self.isPlayerVehicle():
            self.vehId = ribbon.getVehicleID()
            self.ribbonType = ribbon.getType()
            curType = self.vehicles[self.vehId][self.ribbonType]
            if ribbon.getID() == curType['ID']:
                curType['value'] = ribbon.getExtraValue() - curType.get('prevUpdateValue', curType['value'])
                curType['prevUpdateValue'] = ribbon.getExtraValue()
                curType['sum'] += curType['value']
                curType['count'] += 1
                self.updateData()

            # log('stun = %s' % (filter(lambda x: not x.startswith('_'), dir(ribbon))))

    def ribbonAdded(self, ribbon):
        if self.isPlayerVehicle():
            self.vehId = ribbon.getVehicleID()
            if self.vehId in self.vehicles:
                curVeh = self.vehicles[self.vehId]
                self.ribbonType = ribbon.getType()
                if self.ribbonType in curVeh:
                    curType = curVeh[self.ribbonType]
                    curType['value'] = ribbon.getExtraValue()
                    curType['sum'] = curType.setdefault('sum', 0) + curType['value']
                    curType['ID'] = ribbon.getID()
                    curType['count'] += 1
                else:
                    curVeh[self.ribbonType] = {'value':  ribbon.getExtraValue(),
                                               'sum': ribbon.getExtraValue(),
                                               'ID': ribbon.getID(),
                                               'count': 1}
            else:
                self.ribbonType = ribbon.getType()
                self.vehicles[self.vehId] = {self.ribbonType: {'value':  ribbon.getExtraValue(),
                                                               'sum': ribbon.getExtraValue(),
                                                               'ID': ribbon.getID(),
                                                               'count': 1}}
            self.updateData()
                    # log('stun   = %s' % (filter(lambda x: not x.startswith('_'), dir(ribbon))))


_data = DataAssistLog()


class AssistLog(object):

    def __init__(self, section):
        self.section = section
        self.numberLine = {}
        self.listLog = []
        self.countLines = 0
        self.maxCountLines = None
        # self.numberLine = 0
        self.S_GROUP_HITS_PLAYER = section + GROUP_HITS_PLAYER
        self.S_ADD_TO_END = section + ADD_TO_END
        self.S_LINES = section + LINES
        self.S_FORMAT_HISTORY = section + FORMAT_HISTORY
        self.S_MOVE_IN_BATTLE = section + MOVE_IN_BATTLE
        self.S_X = section + 'x'
        self.S_Y = section + 'y'
        self._data = None
        if config.get(self.S_MOVE_IN_BATTLE, False):
            _data = userprefs.get('assistLog/log', {'x': config.get(self.S_X, DEFAULT_X), 'y': config.get(self.S_Y, DEFAULT_Y)})
            if section == SECTION_LOG:
                as_callback("assistLog_mouseDown", self.mouse_down)
                as_callback("assistLog_mouseUp", self.mouse_up)
                as_callback("assistLog_mouseMove", self.mouse_move)
        else:
            _data = {'x': config.get(self.S_X, DEFAULT_X), 'y': config.get(self.S_Y, DEFAULT_Y)}
        self.x = _data['x']
        self.y = _data['y']

    def reset(self):
        self.numberLine = {}
        self.listLog = []
        self.countLines = 0
        self.maxCountLines = None
        # self.numberLine = 0
        if (None not in [self.x, self.y]) and config.get(self.S_MOVE_IN_BATTLE, False) and (self.section == SECTION_LOG):
            userprefs.set('assistLog/log', {'x': self.x, 'y': self.y})

    def mouse_down(self, _data):
        if _data['buttonIdx'] == 0:
            self._data = _data

    def mouse_up(self, _data):
        if _data['buttonIdx'] == 0:
            self._data = None

    def mouse_move(self, _data):
        if self._data:
            self.x += (_data['x'] - self._data['x'])
            self.y += (_data['y'] - self._data['y'])
            as_event('ON_ASSIST_LOG')

    def updateList(self, playerData, mode):
        updateValueMacros(self.section, _data.data)
        if mode == APPEND:
            self.listLog.append(parser(config.get(self.S_FORMAT_HISTORY, '')))
        elif mode == INSERT:
            self.listLog.insert(0, parser(config.get(self.S_FORMAT_HISTORY, '')))
        elif mode == CHANGE:
            self.listLog[playerData] = parser(config.get(self.S_FORMAT_HISTORY, ''))
        if (self.section == SECTION_LOG) or (self.section == SECTION_ALT_LOG):
            if not config.get(self.S_MOVE_IN_BATTLE, False):
                self.x = parser(config.get(self.S_X, DEFAULT_X))
                self.y = parser(config.get(self.S_Y, DEFAULT_Y))

    def isOneLine(self):
        if self.maxCountLines == 0:
            return True
        if self.maxCountLines == 1:
            if self.countLines == 1:
                self.listLog[0] = parser(config.get(self.S_FORMAT_HISTORY, ''))
            else:
                self.listLog.append(parser(config.get(self.S_FORMAT_HISTORY, '')))
            return True
        return False

    def updatePlayers(self, vehID):
        if self.isOneLine():
            return
        elif self.isAddToEnd:
            if self.numberLine[vehID] == self.countLines - 1:
                self.updateList(self.numberLine[vehID], CHANGE)
            else:
                if (self.numberLine[vehID] >= 0) and (self.numberLine[vehID] < self.countLines):
                    self.listLog.pop(self.numberLine[vehID])
                # log('self.numberLine = {}'.format(self.numberLine))
                for v in self.numberLine.iterkeys():
                    if self.numberLine[v] > self.numberLine[vehID]:
                        self.numberLine[v] -= 1
                self.numberLine[vehID] = self.countLines - 1
                self.updateList(self.numberLine[vehID], APPEND)
        else:
            if self.numberLine[vehID] == 0:
                self.updateList(self.numberLine[vehID], CHANGE)
            else:
                if (self.numberLine[vehID] > 0) and (self.numberLine[vehID] < self.countLines):
                    self.listLog.pop(self.numberLine[vehID])
                for v in self.numberLine.iterkeys():
                    if self.numberLine[v] < self.numberLine[vehID]:
                        self.numberLine[v] += 1
                self.numberLine[vehID] = 0
                self.updateList(self.numberLine[vehID], INSERT)

    def addPlayers(self, vehID):
        if self.isOneLine():
            return
        elif self.isAddToEnd:
            _numberLine = self.countLines if self.countLines < self.maxCountLines else (self.maxCountLines - 1)
            if self.countLines >= self.maxCountLines:
                if 0 < self.countLines:
                    self.listLog.pop(0)
                for v in self.numberLine.iterkeys():
                    self.numberLine[v] -= 1
            self.numberLine[vehID] = _numberLine
            self.updateList(self.numberLine[vehID], APPEND)
        else:
            if self.countLines >= self.maxCountLines:
                if 0 < self.countLines:
                    self.listLog.pop(self.countLines - 1)
            for v in self.numberLine.iterkeys():
                self.numberLine[v] += 1
            self.numberLine[vehID] = 0
            self.updateList(self.numberLine[vehID], INSERT)

    def groupHitsPlayer(self):
        vehID = _data.data['vehicleID']
        if vehID in self.numberLine:
            self.updatePlayers(vehID)
        else:
            self.addPlayers(vehID)

    def notGroupHitsPlayer(self):
        updateValueMacros(self.section, _data.data)
        if self.isOneLine():
            return
        if self.isAddToEnd:
            if self.countLines >= self.maxCountLines and 0 < self.countLines:
                self.listLog.pop(0)
            self.listLog.append(parser(config.get(self.S_FORMAT_HISTORY, '')))
        else:
            if self.countLines >= self.maxCountLines and 0 < self.countLines:
                self.listLog.pop(self.countLines - 1)
            self.listLog.insert(0, parser(config.get(self.S_FORMAT_HISTORY, '')))

    def output(self):
        self.countLines = len(self.listLog)
        self.maxCountLines = config.get(self.S_LINES, 7)
        # log('maxCountLines = %s' % self.maxCountLines)
        if not self.maxCountLines:
            return
        self.isAddToEnd = config.get(self.S_ADD_TO_END, False)
        if config.get(self.S_GROUP_HITS_PLAYER, True):
            self.groupHitsPlayer()
        else:
            self.notGroupHitsPlayer()
        # log('listLog = %s' % '\n'.join(self.listLog))
        if self.callEvent:
            as_event('ON_ASSIST_LOG')


_log = AssistLog(SECTION_LOG)
_altLog = AssistLog(SECTION_ALT_LOG)
_backgroundLog = AssistLog(SECTION_BACKGROUND)
_altBackgroundLog = AssistLog(SECTION_ALT_BACKGROUND)


@registerEvent(Vehicle, '_Vehicle__onAppearanceReady')
def _Vehicle__onAppearanceReady(self, appearance):
    if self.isPlayerVehicle and battle.isBattleTypeSupported:
        global chooseRating
        scale = config.networkServicesSettings.scale
        name = config.networkServicesSettings.rating
        r = '{}_{}'.format(scale, name)
        if r in RATINGS:
            chooseRating = RATINGS[r]['name']
        else:
            chooseRating = 'xwgr' if scale == 'xvm' else 'wgr'
        _data.onAppearanceReady(self)


@registerEvent(BattleRibbonsPanel, '_BattleRibbonsPanel__onRibbonUpdated')
def BattleRibbonsPanel__onRibbonUpdated(self, ribbon):
    if ribbon.getType() in ALL_ASSIST and battle.isBattleTypeSupported:
        _data.ribbonUpdated(ribbon)
        # log('assistTrack = %s' % (filter(lambda x: not x.startswith('_'), dir(ribbon))))
        # log('getDamageSource = %s' % ribbon.getDamageSource())
        # log('getExtraValue = %s' % ribbon.getExtraValue())
        # log('getID = %s' % ribbon.getID())
        # log('getType = %s' % ribbon.getType())
        # log('getVehicleID = %s' % ribbon.getVehicleID())


@registerEvent(BattleRibbonsPanel, '_BattleRibbonsPanel__onRibbonAdded')
def BattleRibbonsPanel__onRibbonAdded(self, ribbon):
    if ribbon.getType() in ALL_ASSIST and battle.isBattleTypeSupported:
        _data.ribbonAdded(ribbon)
        # log('assistTrack = %s' % (filter(lambda x: not x.startswith('_'), dir(ribbon))))
        # log('getDamageSource = %s' % ribbon.getDamageSource())
        # log('getExtraValue = %s' % ribbon.getExtraValue())
        # log('getID = %s' % ribbon.getID())
        # log('getType = %s' % ribbon.getType())
        # log('getVehicleID = %s' % ribbon.getVehicleID())


@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    if config.get(ENABLED, True) and battle.isBattleTypeSupported:
        _data.reset()
        _log.reset()
        _altLog.reset()
        _backgroundLog.reset()
        _altBackgroundLog.reset()


@registerEvent(game, 'handleKeyEvent')
def game_handleKeyEvent(event):
    global isDownAlt
    if config.get(ENABLED, True) and battle.isBattleTypeSupported:
        isDown, key, mods, isRepeat = game.convertKeyEvent(event)
        hotkey = config.get('hotkeys/assistLogAltMode', HOTKEYS)
        if hotkey['enabled'] and (key == hotkey['keyCode']):
            if hotkey['onHold']:
                if isDown:
                    if not isDownAlt:
                        isDownAlt = True
                        as_event('ON_ASSIST_LOG')
                else:
                    if isDownAlt:
                        isDownAlt = False
                        as_event('ON_ASSIST_LOG')
            else:
                if isDown:
                    isDownAlt = not isDownAlt
                    as_event('ON_ASSIST_LOG')


def getLog():
    return '\n'.join(_altLog.listLog) if isDownAlt else '\n'.join(_log.listLog)


def getBackgroundLog():
    return '\n'.join(_altBackgroundLog.listLog) if isDownAlt else '\n'.join(_backgroundLog.listLog)


def getLogX():
    return _log.x


def getLogY():
    return _log.y