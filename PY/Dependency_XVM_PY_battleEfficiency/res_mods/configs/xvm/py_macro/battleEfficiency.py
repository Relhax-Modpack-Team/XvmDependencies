import traceback
from BigWorld import player
from re import sub
from math import log
from Avatar import PlayerAvatar
from items import vehicles
from constants import ARENA_BONUS_TYPE
from gui.Scaleform.daapi.view.battle_results_window import BattleResultsWindow
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel
from xfw import registerEvent, overrideMethod
from xfw_actionscript.python import as_event
from xvm_main.python import config, utils, stats, vehinfo
from xvm_main.python.xvm import l10n
from xvm_main.python.consts import DYNAMIC_VALUE_TYPE

battleEfficiencyConfig = config.get('battleEfficiency', {
    'enabled': False,
    'battleResultsWindow': {
        'enabled': False
    }
})

def _getL10n(text):
    if text.find('{{l10n:') > -1:
        return l10n(text)
    return text

def _getScaledDynamicColorValue(rating, value):
    return utils.getDynamicColorValue(DYNAMIC_VALUE_TYPE.X, value)

###

class efficiencyCalculator(object):

    avgTier = 5 #Cache. Can be cached in battles and first battleResultsWindow shows only

    def __init__(self):
        self.tankExpd = {}
        self.vehCD = None
        self.vInfoOK = False

    def reset(self):
        self.__init__()

    def setAvgTier(self):
        plName = player().name
        if stats._stat.resp and (plName in stats._stat.resp.get('players', {})):
            plStats = stats._stat.resp['players'].get(plName)
            self.avgTier = plStats.get('avglvl', 5)

    def registerVInfoData(self, vehCD):
        self.vehCD = vehCD
        vInfoData = vehinfo.getVehicleInfoData(vehCD)
        
        for item in ('wn8expDamage', 'wn8expSpot', 'wn8expFrag', 'wn8expDef', 'wn8expWinRate'):
            self.tankExpd[item] = vInfoData.get(item, None)
        
        self.vInfoOK = None not in self.tankExpd.values()
        if self.vInfoOK:
            self.setAvgTier()

    def calc(self, damage, spotted, frags, defence, capture, isWin = False):
        if self.vInfoOK:
            rDAMAGE = float(damage) / float(self.tankExpd['wn8expDamage'])
            rSPOT = float(spotted) / float(self.tankExpd['wn8expSpot'])
            rFRAG = float(frags) / float(self.tankExpd['wn8expFrag'])
            rDEF = float(defence) / float(self.tankExpd['wn8expDef'])
            rWIN = (100.0 if isWin else 0) / float(self.tankExpd['wn8expWinRate'])
            
            rDAMAGEc = max(0.0, (rDAMAGE - 0.22) / (1 - 0.22))
            rSPOTc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rSPOT - 0.38) / (1 - 0.38))))
            rFRAGc = max(0.0, min(rDAMAGEc + 0.2, max(0.0, (rFRAG - 0.12) / (1 - 0.12))))
            rDEFc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rDEF - 0.10) / (1 - 0.10))))
            rWINc = max(0.0, (rWIN - 0.71) / (1 - 0.71))
            
            WN8 = int(980 * rDAMAGEc + 210 * rDAMAGEc * rFRAGc + 155 * rFRAGc * rSPOTc + 75 * rDEFc * rFRAGc + 145 * min(1.8, rWINc))
            XWN8 = vehinfo.calculateXvmScale('wn8', WN8)
            DIFFExpDmg = int(damage - self.tankExpd['wn8expDamage'])
        else:
            WN8 = 0
            XWN8 = 0
            DIFFExpDmg = 0
        
        EFF = int(max(0, int(damage * (10.0 / (self.avgTier + 2)) * (0.23 + 2 * self.avgTier / 100.0) + frags * 250 + spotted * 150 + log(capture + 1, 1.732) * 150 + defence * 150)))
        XEFF = vehinfo.calculateXvmScale('eff', EFF)
        
        if self.vehCD is not None:
            XTE = vehinfo.calculateXTE(self.vehCD, damage, frags)
        else:
            XTE = 0
        
        return (WN8, XWN8, EFF, XEFF, XTE, DIFFExpDmg)

efficiencyCalculator = efficiencyCalculator()

###

class battleEfficiency(object):

    def __init__(self):
        self.frags = 0
        self.damage = 0
        self.spotted = 0
        self.defence = 0
        self.capture = 0
        self.WN8 = 0
        self.XWN8 = 0
        self.EFF = 0
        self.XEFF = 0
        self.XTE = 0
        self.DIFFExpDmg = 0
        self.DIFFColors = {
            'bad': '#FE0E00',
            'good': '#60FF00'
        }
        self.pickColors()

    def reset(self):
        self.__init__()

    def pickColors(self):
        self.WN8Color = _getScaledDynamicColorValue('wn8', self.XWN8)
        self.EFFColor = _getScaledDynamicColorValue('eff', self.XEFF)
        self.XTEColor = _getScaledDynamicColorValue('x', self.XTE)
        self.DIFFExpDmgColor = self.DIFFColors['bad'] if self.DIFFExpDmg <= 0 else self.DIFFColors['good']

    def update(self):
        calcResult = efficiencyCalculator.calc(self.damage, self.spotted, self.frags, self.defence, self.capture)
        self.WN8, self.XWN8, self.EFF, self.XEFF, self.XTE, self.DIFFExpDmg = calcResult
        self.pickColors()
        as_event('ON_BATTLE_EFFICIENCY')

battleEfficiency = battleEfficiency()

###

@registerEvent(PlayerAvatar, 'vehicle_onAppearanceReady')
def vehicle_onAppearanceReady(self, vehicle):
    if not battleEfficiencyConfig['enabled']:
        return
    
    if vehicle.id == self.playerVehicleID:
        efficiencyCalculator.registerVInfoData(vehicle.typeDescriptor.type.compactDescr)

@overrideMethod(RibbonsAggregator, 'suspend')
def suspend(base, self):
    if not battleEfficiencyConfig['enabled']:
        base(self)
        return
    
    self.resume()

@registerEvent(BattleRibbonsPanel, '_addRibbon')
def _addRibbon(self, ribbonID, ribbonType='', leftFieldStr='', **_):
    if not battleEfficiencyConfig['enabled']:
        return
    
    if ribbonType not in (BATTLE_EFFICIENCY_TYPES.DETECTION, BATTLE_EFFICIENCY_TYPES.DESTRUCTION, BATTLE_EFFICIENCY_TYPES.DEFENCE, BATTLE_EFFICIENCY_TYPES.CAPTURE):
        return
    
    if ribbonType == BATTLE_EFFICIENCY_TYPES.DETECTION:
        battleEfficiency.spotted += 1 if (len(leftFieldStr.strip()) == 0) else int(leftFieldStr[1:])
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DESTRUCTION:
        battleEfficiency.frags += 1
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DEFENCE:
        battleEfficiency.defence = min(100, battleEfficiency.defence + int(leftFieldStr))
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.CAPTURE:
        battleEfficiency.capture = int(leftFieldStr)
    
    battleEfficiency.update()

@registerEvent(DamageLogPanel, '_onTotalEfficiencyUpdated')
def _onTotalEfficiencyUpdated(self, diff):
    if not battleEfficiencyConfig['enabled']:
        return
    
    if PERSONAL_EFFICIENCY_TYPE.DAMAGE in diff:
        battleEfficiency.damage = diff[PERSONAL_EFFICIENCY_TYPE.DAMAGE]
        battleEfficiency.update()

@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def __destroyGUI(self):
    if not battleEfficiencyConfig['enabled']:
        return
    
    battleEfficiency.reset()
    efficiencyCalculator.reset()

###

DEF_RESULTS_LEN = 16
RANKED_OFFSET = 4

DATA_IDS = {
    'damageDealt': 3,
    'spotted': 11,
    'kills': 12,
    'defAndCap_vehWOStun': 14,
    'defAndCap_vehWStun': 17
}

def getDataIDs(offset):
    if not offset:
        return DATA_IDS
    else:
        return {key: value + offset for key, value in DATA_IDS.iteritems()}

@overrideMethod(BattleResultsWindow, 'as_setDataS')
def as_setDataS(base, self, data):
    if not (battleEfficiencyConfig['enabled'] and battleEfficiencyConfig['battleResultsWindow']['enabled']):
        return base(self, data)
    
    def _normalizeString(s):
        return sub('<.*?>', '', s.replace('\xc2\xa0', '').replace('.', '').replace(',', ''))
    
    def _splitArenaStr(s):
        _s = s.replace(u'\xa0\u2014', '-').replace(u'\u2013', '-')
        _s = _s.split('-')
        return _s if (len(_s) == 2) else (s, '')
    
    try:
        common = data['common']
        if common['bonusType'] in (ARENA_BONUS_TYPE.EVENT_BATTLES, ARENA_BONUS_TYPE.EPIC_RANDOM, ARENA_BONUS_TYPE.EPIC_RANDOM_TRAINING, ARENA_BONUS_TYPE.EPIC_BATTLE):
            return base(self, data)
        
        offset = 0 if common['bonusType'] != ARENA_BONUS_TYPE.RANKED else RANKED_OFFSET
        
        teamDict = data['team1']
        statValues = data['personal']['statValues'][0]
        stunStatus = 'vehWStun' if (len(statValues) > (DEF_RESULTS_LEN + offset)) else 'vehWOStun' #it is complicated to get stun info for vehicle not in battle
        isWin = common['resultShortStr'] == 'win'
        arenaStr = _splitArenaStr(common['arenaStr'])
        mapName = arenaStr[0].strip()
        battleType = arenaStr[1].strip()
        
        for playerDict in teamDict:
            if playerDict['isSelf']:
                efficiencyCalculator.registerVInfoData(playerDict['vehicleCD'])
                break
        
        dataIDs = getDataIDs(offset)
        damageDealt = _normalizeString(statValues[dataIDs['damageDealt']]['value'])
        spotted = _normalizeString(statValues[dataIDs['spotted']]['value'])
        kills = _normalizeString(statValues[dataIDs['kills']]['value']).split('/')
        kills = kills[1]
        defAndCap = _normalizeString(statValues[dataIDs['defAndCap_' + stunStatus]]['value']).split('/')
        capture = defAndCap[0]
        defence = defAndCap[1]
        
        calcResult = efficiencyCalculator.calc(int(damageDealt), int(spotted), int(kills), int(defence), int(capture), isWin)
        WN8, XWN8, EFF, XEFF, XTE, _ = calcResult
        
        textFormat = _getL10n(battleEfficiencyConfig['battleResultsWindow']['textFormat']) 
        textFormat = textFormat.replace('{{mapName}}', mapName)
        textFormat = textFormat.replace('{{battleType}}', battleType)
        textFormat = textFormat.replace('{{wn8}}', str(WN8))
        textFormat = textFormat.replace('{{xwn8}}', str(XWN8))
        textFormat = textFormat.replace('{{eff}}', str(EFF))
        textFormat = textFormat.replace('{{xeff}}', str(XEFF))
        textFormat = textFormat.replace('{{xte}}', str(XTE))
        textFormat = textFormat.replace('{{c:wn8}}', _getScaledDynamicColorValue('wn8', XWN8))
        textFormat = textFormat.replace('{{c:eff}}', _getScaledDynamicColorValue('eff', XEFF))
        textFormat = textFormat.replace('{{c:xte}}', _getScaledDynamicColorValue('x', XTE))
        
        data['common']['arenaStr'] = textFormat
    except:
        traceback.print_exc()
        data['common']['arenaStr'] += '  <font color="#FE0E00">efficiency error!</font>'
    
    efficiencyCalculator.reset()
    return base(self, data)

###

@xvm.export('efficiency.damage', deterministic=False)
def efficiencyDamage():
    return battleEfficiency.damage

@xvm.export('efficiency.wn8', deterministic=False)
def efficiencyWN8():
    return battleEfficiency.WN8

@xvm.export('efficiency.xwn8', deterministic=False)
def efficiencyXWN8():
    return battleEfficiency.XWN8

@xvm.export('efficiency.eff', deterministic=False)
def efficiencyEFF():
    return battleEfficiency.EFF

@xvm.export('efficiency.xeff', deterministic=False)
def efficiencyXEFF():
    return battleEfficiency.XEFF

@xvm.export('efficiency.xte', deterministic=False)
def efficiencyXTE():
    return battleEfficiency.XTE

@xvm.export('efficiency.diffExpDmg', deterministic=False)
def efficiencyDIFFExpDmg():
    return battleEfficiency.DIFFExpDmg

@xvm.export('efficiency.diffAvgDmg', deterministic=False)
def efficiencyDIFFAvgDmg(avgDmg = None, minus = '', plus = ''):
    if avgDmg is not None:
        DIFFAvgDmg = int(battleEfficiency.damage - avgDmg)
        return '{}{}'.format(minus, DIFFAvgDmg) if DIFFAvgDmg <= 0 else '{}{}'.format(plus, DIFFAvgDmg)

@xvm.export('efficiency.wn8Color', deterministic=False)
def efficiencyWN8Color():
    return battleEfficiency.WN8Color

@xvm.export('efficiency.effColor', deterministic=False)
def efficiencyEFFColor():
    return battleEfficiency.EFFColor

@xvm.export('efficiency.xteColor', deterministic=False)
def efficiencyXTEColor():
    return battleEfficiency.XTEColor

@xvm.export('efficiency.diffExpDmgColor', deterministic=False)
def efficiencyDIFFExpDmgColor():
    return battleEfficiency.DIFFExpDmgColor

@xvm.export('efficiency.diffAvgDmgColor', deterministic=False)
def efficiencyDIFFAvgDmgColor(avgDmg = None):
    if avgDmg is not None:
        DIFFAvgDmgValue = int(battleEfficiency.damage - avgDmg)
        return battleEfficiency.DIFFColors['bad'] if DIFFAvgDmgValue <= 0 else battleEfficiency.DIFFColors['good']
