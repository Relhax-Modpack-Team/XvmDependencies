import ResMgr
import nations
from Avatar import PlayerAvatar
from AvatarInputHandler import AvatarInputHandler
from Vehicle import Vehicle
from aih_constants import CTRL_MODE_NAME
from constants import ITEM_DEFS_PATH
from gui.Scaleform.daapi.view.battle.shared.consumables_panel import ConsumablesPanel
from helpers import dependency
from items import _xml, vehicles
from skeletons.gui.battle_session import IBattleSessionProvider

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
from xfw.events import registerEvent
from xfw_actionscript.python import as_event
from xvm_main.python.logger import *

SHELL_TYPES = {'armor_piercing': '{{l10n:armor_piercing}}',
               'high_explosive': '{{l10n:high_explosive}}',
               'armor_piercing_cr': '{{l10n:armor_piercing_cr}}',
               'armor_piercing_he': '{{l10n:armor_piercing_he}}',
               'hollow_charge': '{{l10n:hollow_charge}}'}

DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]

gold_shells = {}
xmlPath = ''
shellType = None
shellSpeed = None
shellsSpeed = {}
goldShell = None
piercingPower = None
explosionRadius = None
damage = None
caliber = None
isLastShot = False
quantityShells = {}
visible = True

for nation in nations.NAMES:
    xmlPath = '%s%s%s%s' % (ITEM_DEFS_PATH, 'vehicles/', nation, '/components/shells.xml')
    xmlCtx_s = (((None, '{}/{}'.format(xmlPath, n)), s) for n, s in ResMgr.openSection(xmlPath).items() if (n != 'icons') and (n != 'xmlns:xmlref'))
    gold_shells[nation] = [_xml.readInt(xmlCtx, s, 'id', 0, 65535) for xmlCtx, s in xmlCtx_s if s.readBool('improved', False)]

ResMgr.purge(xmlPath, True)


def reset(isDead=False):
    global shellType, goldShell, shellSpeed, shellsSpeed, piercingPower, explosionRadius, damage, caliber, quantityShells
    if isDead:
        shellType = None
        shellsSpeed = {}
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


def updateCurrentShell(intCD, ammoCtrl):
    global shellType, explosionRadius, damage, piercingPower, shellSpeed, goldShell, caliber
    shotDescr = vehicles.getItemByCompactDescr(intCD)
    shellType = config.get('sight/shellType', SHELL_TYPES).get(shotDescr.kind.lower(), None)
    explosionRadius = shotDescr.type.explosionRadius if hasattr(shotDescr.type, 'explosionRadius') else None
    damage = shotDescr.damage[0]
    gunSetting = ammoCtrl.getGunSettings()
    piercingPower = gunSetting.getPiercingPower(intCD)
    caliber = shotDescr.caliber
    goldShell = 'gold' if shotDescr.id[1] in gold_shells[nations.NAMES[shotDescr.id[0]]] else None
    shellSpeed = shellsSpeed.get(intCD, None)


def shellsUpdatedOrAdd(intCD, quantity):
    global quantityShells, isLastShot
    sessionProvider = dependency.instance(IBattleSessionProvider)
    quantityShells[intCD] = quantity
    quantity = sum(quantityShells.itervalues())
    isLastShot = quantity <= 1
    ammoCtrl = sessionProvider.shared.ammo
    CurrentShellCD = ammoCtrl.getCurrentShellCD()
    if CurrentShellCD is None and ammoCtrl._order:
        CurrentShellCD = ammoCtrl._order[0]
    if isLastShot:
        reset()
    elif CurrentShellCD == intCD:
        updateCurrentShell(intCD, ammoCtrl)
    as_event('ON_AMMO_CHANGED')


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    newVisible = eMode in DISPLAY_IN_MODES
    if newVisible != visible:
        visible = newVisible
        as_event('ON_AMMO_CHANGED')


@registerEvent(ConsumablesPanel, '_onShellsAdded')
def infoChargedShell_onShellsAdded(self, intCD, descriptor, quantity, _, gunSettings):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        shellsUpdatedOrAdd(intCD, quantity)


@registerEvent(ConsumablesPanel, '_onShellsUpdated')
def infoChargedShell_onShellsUpdated(self, intCD, quantity, *args):
    global quantityShells
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        shellsUpdatedOrAdd(intCD, quantity)


@registerEvent(ConsumablesPanel, '_onCurrentShellChanged')
def infoChargedShell_onCurrentShellChanged(self, intCD):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        if isLastShot:
            return reset()
        else:
            updateCurrentShell(intCD, self.sessionProvider.shared.ammo)
        as_event('ON_AMMO_CHANGED')


@registerEvent(Vehicle, '_Vehicle__onAppearanceReady')
def _Vehicle__onAppearanceReady(self, appearance):
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global visible, shellsSpeed
        shellsSpeed = {shot.shell.compactDescr: int(shot.speed * 1.25) for shot in self.typeDescriptor.gun.shots}
        visible = True


@registerEvent(PlayerAvatar, 'updateVehicleHealth')
def PlayerAvatar_updateVehicleHealth(self, vehicleID, health, deathReasonID, isCrewActive, isRespawn):
    if not (health > 0 and isCrewActive) and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        reset(True)


@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    reset(True)


@xvm.export('sight.shellType', deterministic=False)
def sight_shellType():
    return shellType if visible else None


@xvm.export('sight.shellSpeed', deterministic=False)
def sight_shellSpeed():
    return shellSpeed if visible else None


@xvm.export('sight.goldShell', deterministic=False)
def sight_goldShell():
    return goldShell if visible else None


@xvm.export('sight.piercingShell', deterministic=False)
def sight_piercingPower():
    return piercingPower if visible else None


@xvm.export('sight.explosionRadiusShell', deterministic=False)
def sight_explosionRadius():
    return explosionRadius if visible else None


@xvm.export('sight.damageShell', deterministic=False)
def sight_damage():
    return damage if visible else None


@xvm.export('sight.caliberShell', deterministic=False)
def sight_caliber():
    return caliber if visible else None
