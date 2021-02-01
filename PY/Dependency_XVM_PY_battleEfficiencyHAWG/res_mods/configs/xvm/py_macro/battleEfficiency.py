from BigWorld import player
from xfw import registerEvent
from xfw_actionscript.python import as_event
from xvm_main.python import utils, stats, consts, vehinfo
from Avatar import PlayerAvatar
from math import log as mathLog
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES as BET
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel

class battleEfficiency(object):

    def __init__(self):
        self.vehCD = None
        self.tankExpd = {}
        self.tankExists = False
        self.frags = 0
        self.damage = 0
        self.spotted = 0
        self.defence = 0
        self.capture = 0
        self.WN8 = 0
        self.EFF = 0
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
        self.WN8Color = utils.getDynamicColorValue(consts.DYNAMIC_VALUE_TYPE.WN8, self.WN8)
        self.EFFColor = utils.getDynamicColorValue(consts.DYNAMIC_VALUE_TYPE.EFF, self.EFF)
        self.XTEColor = utils.getDynamicColorValue(consts.DYNAMIC_VALUE_TYPE.X, self.XTE)
        self.DIFFExpDmgColor = self.DIFFColors['bad'] if self.DIFFExpDmg <= 0 else self.DIFFColors['good']

    def calcEfficiency(self):
        if self.tankExists:
            rDAMAGE = float(self.damage) / float(self.tankExpd['wn8expDamage'])
            rSPOT = float(self.spotted) / float(self.tankExpd['wn8expSpot'])
            rFRAG = float(self.frags) / float(self.tankExpd['wn8expFrag'])
            rDEF = float(self.defence) / float(self.tankExpd['wn8expDef'])
            rWIN = 0
            
            rDAMAGEc = max(0.0, (rDAMAGE - 0.22) / (1 - 0.22))
            rSPOTc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rSPOT - 0.38) / (1 - 0.38))))
            rFRAGc = max(0.0, min(rDAMAGEc + 0.2, max(0.0, (rFRAG - 0.12) / (1 - 0.12))))
            rDEFc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rDEF - 0.10) / (1 - 0.10))))
            rWINc = max(0.0, (rWIN - 0.71) / (1 - 0.71))
            
            self.WN8 = int(980 * rDAMAGEc + 210 * rDAMAGEc * rFRAGc + 155 * rFRAGc * rSPOTc + 75 * rDEFc * rFRAGc + 145 * min(1.8, rWINc))
            self.DIFFExpDmg = int(self.damage - self.tankExpd['wn8expDamage'])
        else:
            self.WN8 = 0
            self.DIFFExpDmg = 0
        try:
            avgTier = float(stats._stat.resp['players'].get(player().name)['lvl'])
        except:
            avgTier = 5
        self.EFF = int(max(0, int(self.damage * (10 / (avgTier + 2)) * (0.23 + 2 * avgTier / 100.0) + self.frags * 250 + self.spotted * 150 + mathLog(self.capture + 1, 1.732) * 150 + self.defence * 150)))
        self.XTE = vehinfo.calculateXTE(self.vehCD, self.damage, self.frags)

    def update(self):
        self.calcEfficiency()
        self.pickColors()
        as_event('ON_BATTLE_EFFICIENCY')

battleEff = battleEfficiency()


###

@registerEvent(BattleRibbonsPanel, '_addRibbon')
def _addRibbon(self, ribbonID, ribbonType='', leftFieldStr='', vehName='', vehType='', rightFieldStr='', bonusRibbonLabelID=''):
    if ribbonType not in [BET.DETECTION, BET.DESTRUCTION, BET.DEFENCE, BET.CAPTURE]:
        return
    
    if ribbonType == BET.DETECTION:
        if len(leftFieldStr.strip()) == 0:
            battleEff.spotted += 1
        else:
            battleEff.spotted += int(leftFieldStr[1:])
    elif ribbonType == BET.DESTRUCTION:
        battleEff.frags += 1
    elif ribbonType == BET.DEFENCE:
        battleEff.defence += int(leftFieldStr)
    elif ribbonType == BET.CAPTURE:
        battleEff.capture = int(leftFieldStr)
    
    battleEff.update()

@registerEvent(DamageLogPanel, '_onTotalEfficiencyUpdated')
def _onTotalEfficiencyUpdated(self, diff):
    if PERSONAL_EFFICIENCY_TYPE.DAMAGE in diff:
        battleEff.damage = diff[PERSONAL_EFFICIENCY_TYPE.DAMAGE]
        battleEff.update()

@registerEvent(PlayerAvatar, 'vehicle_onEnterWorld')
def vehicle_onEnterWorld(self, vehicle):
    if vehicle.id == self.playerVehicleID:
        battleEff.vehCD = vehicle.typeDescriptor.type.compactDescr
        vehicleInfoData = vehinfo.getVehicleInfoData(battleEff.vehCD)
        battleEff.tankExpd['wn8expDamage'] = vehicleInfoData.get('wn8expDamage', None)
        battleEff.tankExpd['wn8expSpot'] = vehicleInfoData.get('wn8expSpot', None)
        battleEff.tankExpd['wn8expDef'] = vehicleInfoData.get('wn8expDef', None)
        battleEff.tankExpd['wn8expFrag'] = vehicleInfoData.get('wn8expFrag', None)
        battleEff.tankExists = None not in battleEff.tankExpd.values()

@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def __destroyGUI(self):
    battleEff.reset()


###

@xvm.export('efficiencyWN8', deterministic=False)
def efficiencyWN8():
    return battleEff.WN8

@xvm.export('efficiencyEFF', deterministic=False)
def efficiencyEFF():
    return battleEff.EFF

@xvm.export('efficiencyXTE', deterministic=False)
def efficiencyXTE():
    return battleEff.XTE

@xvm.export('efficiencyDIFFExpDmg', deterministic=False)
def efficiencyDIFFExpDmg():
    return battleEff.DIFFExpDmg

@xvm.export('efficiencyDIFFAvgDmg', deterministic=False)
def efficiencyDIFFAvgDmg(avgDmg=None, Minus='', Plus=''):
    if avgDmg is not None:
        DIFFAvgDmg = int(battleEff.damage - avgDmg)
        return '{}{}'.format(Minus, DIFFAvgDmg) if DIFFAvgDmg <= 0 else '{}{}'.format(Plus, DIFFAvgDmg)

@xvm.export('efficiencyWN8Color', deterministic=False)
def efficiencyWN8Color():
    return battleEff.WN8Color

@xvm.export('efficiencyEFFColor', deterministic=False)
def efficiencyEFFColor():
    return battleEff.EFFColor

@xvm.export('efficiencyXTEColor', deterministic=False)
def efficiencyXTEColor():
    return battleEff.XTEColor

@xvm.export('efficiencyDIFFExpDmgColor', deterministic=False)
def efficiencyDIFFExpDmgColor():
    return battleEff.DIFFExpDmgColor

@xvm.export('efficiencyDIFFAvgDmgColor', deterministic=False)
def efficiencyDIFFAvgDmgColor(avgDmg=None):
    if avgDmg is not None:
        DIFFAvgDmgValue = int(battleEff.damage - avgDmg)
        return battleEff.DIFFColors['bad'] if DIFFAvgDmgValue <= 0 else battleEff.DIFFColors['good']
