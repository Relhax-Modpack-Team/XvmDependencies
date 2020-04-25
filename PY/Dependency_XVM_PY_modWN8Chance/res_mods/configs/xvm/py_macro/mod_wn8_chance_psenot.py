import BigWorld
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from items.vehicles import getVehicleTypeCompactDescr
from Avatar import PlayerAvatar
from debug_utils import _doLog

import xfw
from xvm_main.python.stats import _stat, _Stat
from xvm_main.python import utils
from xvm_main.python.consts import DYNAMIC_VALUE_TYPE
import xvm_main.python.config as xvm_config
import xvm_main.python.vehinfo as xvm_vehinfo
from xvm_main.python.consts import XVM_COMMAND
from xfw_actionscript.python import as_event


class Config(object):
    def __init__(self):
        self.default = {
            'logLevel': 2,
            'useTankRating': False,
        }
        self.user = {}

    def __getitem__(self, key):
        result = self.get(key, self)
        if result is self:
            raise KeyError(key)
        return result

    def get(self, key, default=None):
        return self.user.get(key, self.default.get(key, default))

    def reload(self):
        self.user = {}

        # try:
        #     with open('res_mods/configs/expected_tank_values.json') as values_file:
        #         self.user['expValues'] = json.load(data_file)
        # except Exception as e:
        #     LOG_WARN('Cannot load expected tank values (%s)' % (e,))

config = Config()

def LOG_ERROR(msg, *kargs, **kwargs):
    if config.get('logLevel', 0) >= 0:
        _doLog('ERROR', msg, kargs, kwargs)

def LOG_WARN(msg, *kargs, **kwargs):
    if config.get('logLevel', 0) >= 1:
        _doLog('WARNING', msg, kargs, kwargs)

def LOG_INFO(msg, *kargs, **kwargs):
    if config.get('logLevel', 0) >= 2:
        _doLog('INFO', msg, kargs, kwargs)

def LOG_DEBUG(msg, *kargs, **kwargs):
    if config.get('logLevel', 0) >= 3:
        _doLog('DEBUG', msg, kargs, kwargs)

def getPlayerStats(vehicleID):
    # Retrieve player rating and associated color
    # FIXME: is there any API to retrieve the cached stats from Python!?
    if _stat.players is not None and vehicleID in _stat.players:
        pl = _stat.players.get(vehicleID)
        cacheKey = "%d=%d" % (pl.accountDBID, pl.vehCD)
        if cacheKey in _stat.cacheBattle:
            return fixStats(_stat.cacheBattle[cacheKey])

    return None

def fixStats(stats):
    if stats is None:
        return None

    stats = stats.copy()
    rating = xvm_config.networkServicesSettings.rating

    if not stats.has_key('xte') and stats.has_key('v') and stats['v'].has_key('xte'):
        stats['xte'] = stats['v']['xte']

    stats['r'] = stats.get(rating, 0)
    stats['xr'] = stats['r'] if rating.startswith('x') else stats.get('x' + rating, 0)
    # stats['cr'] = ChatColor.getRatingColor(stats)

    # Stats for new players are incomplete, so use default values (StatsFormatter does most of the job)
    stats['flag'] = stats.get('flag', 'default')

    return stats

vehicles = {}
enemies_wn8 = 0
allies_wn8 = 0
x = 0

@xvm.export('enemiesAliveRating', deterministic=False)
def enemiesAliveRating():
    return int(enemies_wn8)

@xvm.export('alliesAliveRating', deterministic=False)
def alliesAliveRating():
    return int(allies_wn8)

@xvm.export('alliesAliveRatingRatio', deterministic=False)
def alliesAliveRatingRatio():
    if enemies_wn8 != 0 and allies_wn8 != 0:
        if enemies_wn8 > allies_wn8:
            x = int(50 - (1.0 - allies_wn8 / enemies_wn8) * 50)
        else:
            x = int(50 + (1.0 - enemies_wn8 / allies_wn8) * 50)
    else:
        x = int(0)

    return x


@xvm.export('c_alliesAliveRatingRatio', deterministic=False)
def c_alliesAliveRatingRatio():
    if enemies_wn8 != 0 and allies_wn8 != 0:
        if enemies_wn8 > allies_wn8:
            x = float(50 - (1.0 - allies_wn8 / enemies_wn8) * 50)
            if x > 89.5:
                return '#D042F3'
            elif x > 74.5:
                return '#02C9B3'
            elif x > 59.5:
                return '#60FF00'
            elif x > 39.5:
                return '#F8F400'
            elif x > 24.5:
                return '#FE7903'
            else:
                return '#FE0E00'
        else:
            x = float(50 + (1.0 - enemies_wn8 / allies_wn8) * 50)
            if x > 89.5:
                return '#D042F3'
            elif x > 74.5:
                return '#02C9B3'
            elif x > 59.5:
                return '#60FF00'
            elif x > 39.5:
                return '#F8F400'
            elif x > 24.5:
                return '#FE7903'
            else:
                return '#FE0E00'
    else:
        return '#FFFFFF'
    return


def setVehicleStats(vid, vehicle):
    global enemies_wn8, allies_wn8

    vehicle['stats'] = stats = getPlayerStats(vid)
    if stats is not None:
        vehicle['wn8'] = stats.get('wn8', None)
        info = vehicle['info']

        if config.get('useTankRating', False):
            if 'wn8expDamage' in info and all(k in stats['v'] for k in ('b', 'frg', 'dmg', 'w', 'spo', 'def')):
                if stats['v']['b'] >= 100:
                    # Compute WN8 for that vehicle
                    rDAMAGE = stats['v']['dmg'] / (stats['v']['b'] * info['wn8expDamage'])
                    rSPOT   = stats['v']['spo'] / (stats['v']['b'] * info['wn8expSpot'])
                    rFRAG   = stats['v']['frg'] / (stats['v']['b'] * info['wn8expFrag'])
                    rDEF    = stats['v']['def'] / (stats['v']['b'] * info['wn8expDef'])
                    rWIN    = stats['v']['w']   / (stats['v']['b'] * info['wn8expWinRate']) * 100.0
            
                    rWINc    = max(0,                     (rWIN    - 0.71) / (1 - 0.71) )
                    rDAMAGEc = max(0,                     (rDAMAGE - 0.22) / (1 - 0.22) )
                    rFRAGc   = max(0, min(rDAMAGEc + 0.2, (rFRAG   - 0.12) / (1 - 0.12)))
                    rSPOTc   = max(0, min(rDAMAGEc + 0.1, (rSPOT   - 0.38) / (1 - 0.38)))
                    rDEFc    = max(0, min(rDAMAGEc + 0.1, (rDEF    - 0.10) / (1 - 0.10)))
            
                    WN8 = 980*rDAMAGEc + 210*rDAMAGEc*rFRAGc + 155*rFRAGc*rSPOTc + 75*rDEFc*rFRAGc + 145*min(1.8,rWINc)
            
                    vehicle['wn8'] = WN8

        if vehicle['wn8'] is not None:
            if BigWorld.player().team == vehicle['team']:
                allies_wn8 += float(vehicle['wn8'])
            else:
                enemies_wn8 += float(vehicle['wn8'])



            LOG_DEBUG('ALLIES=%d ENEMIES=%d RATIO=%s' % (allies_wn8, enemies_wn8, (allies_wn8  * 100 / enemies_wn8) if enemies_wn8 != 0 else -1))
            as_event('ON_UPDATE_TEAM_RATING')

def onStatsReady():
    for vid, vehicle in vehicles.iteritems():
        if vehicle.get('stats') is None:
            setVehicleStats(vid, vehicle)
            LOG_DEBUG('%s => %s' % (vid, vehicle))

@xfw.registerEvent(_Stat, '_respond')
def _Stat__respond(self):
    # There is no event when stats are ready, so we have to hook private method of private class
    # for that (we cannot hook xfw.as_xfw_cmd as it is implemented in Flash, even though the method
    # exists in xfw.swf)
    LOG_DEBUG('_Stat._respond(%s)' % (self.req['cmd'],))
    if self.req['cmd'] == XVM_COMMAND.AS_STAT_BATTLE_DATA:
        BigWorld.callback(0, onStatsReady)

@xfw.registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    #LOG_DEBUG('FragsCollectableStats.addVehicleStatusUpdate(%s) [vehCD=%s]' % (vInfoVO, vInfoVO.vehicleType.compactDescr))

    global enemies_wn8, allies_wn8

    if len(vehicles) == 0:
        config.reload()
        enemies_wn8 = allies_wn8 = 0

    vid = vInfoVO.vehicleID
    vehCD = vInfoVO.vehicleType.compactDescr

    is_ally = BigWorld.player().team == vInfoVO.team
    if vInfoVO.isAlive():
        if vid not in vehicles:
            info = xvm_vehinfo.getVehicleInfoData(vehCD)
            vehicle = dict(vehCD=vehCD, info=info, team=vInfoVO.team)
            vehicles[vid] = vehicle
            setVehicleStats(vid, vehicle)
    else:
        if vid in vehicles:
            vehicle = vehicles.pop(vid)

            if vehicle.get('wn8', None) is not None:
                if is_ally:
                    allies_wn8 -= vehicle['wn8']
                else:
                    enemies_wn8 -= vehicle['wn8']

                LOG_DEBUG('ALLIES=%d ENEMIES=%d RATIO=%s' % (allies_wn8, enemies_wn8, (allies_wn8  * 100 / enemies_wn8) if enemies_wn8 != 0 else -1))
                as_event('ON_UPDATE_TEAM_RATING')

@xfw.registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    global vehicles

    # Reset
    vehicles = {}