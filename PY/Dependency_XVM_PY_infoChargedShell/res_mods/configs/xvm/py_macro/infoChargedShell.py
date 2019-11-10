import BigWorld
import ResMgr
import nations
from Vehicle import Vehicle
from Avatar import PlayerAvatar
from items import _xml
from constants import ITEM_DEFS_PATH
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.battle_control.battle_constants import SHELL_SET_RESULT
from gui.Scaleform.daapi.view.battle.shared.consumables_panel import ConsumablesPanel

from xfw import *
from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle


SHELL_TYPES = {'armor_piercing':    '{{l10n:armor_piercing}}',
               'high_explosive':    '{{l10n:high_explosive}}',
               'armor_piercing_cr': '{{l10n:armor_piercing_cr}}',
               'armor_piercing_he': '{{l10n:armor_piercing_he}}',
               'hollow_charge':     '{{l10n:hollow_charge}}'}


gold_shells = {}
xmlPath = ''
shotsDescr = None
shellType = None
shellSpeed = None
goldShell = None
piercingPower = None
explosionRadius = None
damage = None
caliber = None
playerVehicleID = None
isLastShot = False
quantityShells = {}


for nation in nations.NAMES:
    xmlPath = '%s%s%s%s' % (ITEM_DEFS_PATH, 'vehicles/', nation, '/components/shells.xml')
    xmlCtx_s = (((None, '{}/{}'.format(xmlPath, n)), s) for n, s in ResMgr.openSection(xmlPath).items() if (n != 'icons') and (n != 'xmlns:xmlref'))
    gold_shells[nation] = [_xml.readInt(xmlCtx, s, 'id', 0, 65535) for xmlCtx, s in xmlCtx_s if s.readBool('improved', False)]

ResMgr.purge(xmlPath, True)


def reset(isDead=False):
    global shellType, goldShell, shellSpeed, piercingPower, explosionRadius, damage, caliber, shotsDescr, quantityShells
    if isDead:
        shellType = None
        shotsDescr = None
        quantityShells = {}
    else:
        shellType = config.get('sight/shellType/not_shell', '')
    shellSpeed = None
    goldShell = None
    piercingPower = None
    explosionRadius = None
    damage = None
    caliber = None
    as_event('ON_AMMO_CHANGED')


@registerEvent(ConsumablesPanel, '_ConsumablesPanel__onShellsAdded')
def infoChargedShell__onShellsAdded(self, intCD, descriptor, quantity, _, gunSettings):
    global quantityShells
    if battle.isBattleTypeSupported:
        quantityShells[intCD] = quantity


@registerEvent(ConsumablesPanel, '_ConsumablesPanel__onShellsUpdated')
def infoChargedShell__onShellsUpdated(self, intCD, quantity, *args):
    global quantityShells
    if battle.isBattleTypeSupported:
        quantityShells[intCD] = quantity
        if isLastShot or quantity == 0:
            reset()


@registerEvent(ConsumablesPanel, '_ConsumablesPanel__onCurrentShellChanged')
def infoChargedShell__onCurrentShellChanged(self, intCD):
    global isLastShot, shellType, goldShell, shellSpeed, piercingPower, explosionRadius, damage, caliber, shotsDescr
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        ctrl = BigWorld.player().guiSessionProvider.shared.ammo
        shells = ctrl.getOrderedShellsLayout()
        # quantity = sum(shell[2] for shell in shells)
        quantity = sum(quantityShells.itervalues())
        isLastShot = quantity <= 1
        if quantity == 0:
            return reset()
        else:
            if shotsDescr is None:
                ownVehicle = BigWorld.entities.get(BigWorld.player().playerVehicleID, None)
                shotsDescr = ownVehicle.typeDescriptor.gun.shots
            for shell in shells:
                if shell[0] == intCD:
                    shellType = config.get('sight/shellType', SHELL_TYPES).get(shell[1].kind.lower(), None)
                    id = shell[1].id
                    # log('id = %s' % id[1])
                    for shot in shotsDescr:
                        _shell = shot.shell
                        if _shell.id == id:
                            explosionRadius = _shell.type.explosionRadius if hasattr(_shell.type, 'explosionRadius') else None
                            damage = _shell.damage[0]
                            piercingPower = shot.piercingPower[0]
                            shellSpeed = int(shot.speed * 1.25)
                            # log('shellSpeed = %s' % shellSpeed)
                            # log('piercingPower = %s' % piercingPower)
                            caliber = _shell.caliber
                            break
                    goldShell = 'gold' if id[1] in gold_shells[nations.NAMES[id[0]]] else None
                    break
        as_event('ON_AMMO_CHANGED')


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global playerVehicleID #, shotsDescr
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        playerVehicleID = self.id
        # shotsDescr = self.typeDescriptor.gun.shots
        # reset(True)


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    if (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID) and battle.isBattleTypeSupported:
        reset(True)


@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    reset(True)

@xvm.export('sight.shellType', deterministic=False)
def sight_shellType():
    return shellType


@xvm.export('sight.shellSpeed', deterministic=False)
def sight_shellSpeed():
    return shellSpeed


@xvm.export('sight.goldShell', deterministic=False)
def sight_goldShell():
    return goldShell


@xvm.export('sight.piercingShell', deterministic=False)
def sight_piercingPower():
    return piercingPower


@xvm.export('sight.explosionRadiusShell', deterministic=False)
def sight_explosionRadius():
    return explosionRadius


@xvm.export('sight.damageShell', deterministic=False)
def sight_damage():
    return damage


@xvm.export('sight.caliberShell', deterministic=False)
def sight_caliber():
    return caliber
