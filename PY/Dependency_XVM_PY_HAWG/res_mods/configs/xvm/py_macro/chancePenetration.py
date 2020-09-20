import BigWorld
import gui.Scaleform.daapi.view.battle.shared.crosshair.plugins as plug
import math
from Avatar import PlayerAvatar
from AvatarInputHandler import AvatarInputHandler
from AvatarInputHandler.gun_marker_ctrl import _CrosshairShotResults, _SHOT_RESULT
from Vehicle import Vehicle
from aih_constants import CTRL_MODE_NAME

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
from xfw.events import registerEvent, overrideClassMethod
from xfw_actionscript.python import *
from xvm_main.python.logger import *

NOT_PIERCED = 'not_pierced'
LITTLE_PIERCED = 'little_pierced'
GREAT_PIERCED = 'great_pierced'
NOT_TARGET = 'not_target'
DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]

PIERCING_CHANCE_KEY = (None, NOT_PIERCED, LITTLE_PIERCED, GREAT_PIERCED)
COLOR_PIERCING_CHANCE = {NOT_PIERCED: '#E82929',
                         LITTLE_PIERCED: '#E1C300',
                         GREAT_PIERCED: '#2ED12F',
                         NOT_TARGET: ''}

piercingActual = None
armorActual = None
piercingChance = None
shotResult = None
hitAngle = None
normHitAngle = None
colorPiercingChance = COLOR_PIERCING_CHANCE
visible = True


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    newVisible = eMode in DISPLAY_IN_MODES
    if newVisible != visible:
        visible = newVisible
        as_event('ON_CALC_ARMOR')


@registerEvent(plug.ShotResultIndicatorPlugin, '_ShotResultIndicatorPlugin__onGunMarkerStateChanged')
def onGunMarkerStateChanged(self, markerType, position, direction, collision):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        if not self._ShotResultIndicatorPlugin__isEnabled:
            self._ShotResultIndicatorPlugin__shotResultResolver.getShotResult(position, collision, direction,
                                                                              excludeTeam=self._ShotResultIndicatorPlugin__playerTeam)


@overrideClassMethod(_CrosshairShotResults, 'getShotResult')
def _CrosshairShotResults_getShotResult(base, cls, hitPoint, collision, direction, excludeTeam=0, piercingMultiplier=1):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global piercingActual, armorActual, shotResult, hitAngle, normHitAngle, piercingChance
        old_piercingActual = piercingActual
        old_armorActual = armorActual
        old_hitAngle = hitAngle
        piercingActual = None
        armorActual = None
        piercingChance = None
        hitAngle = None
        normHitAngle = None
        shotResult = PIERCING_CHANCE_KEY[_SHOT_RESULT.UNDEFINED]
        if collision is None:
            if (old_armorActual != armorActual) or (old_piercingActual != piercingActual) or (old_hitAngle != hitAngle):
                as_event('ON_CALC_ARMOR')
            return _SHOT_RESULT.UNDEFINED
        entity = collision.entity
        if entity.__class__.__name__ not in ('Vehicle', 'DestructibleEntity'):
            if (old_armorActual != armorActual) or (old_piercingActual != piercingActual) or (old_hitAngle != hitAngle):
                as_event('ON_CALC_ARMOR')
            return _SHOT_RESULT.UNDEFINED
        if entity.health <= 0 or entity.publicInfo['team'] == excludeTeam:
            if (old_armorActual != armorActual) or (old_piercingActual != piercingActual) or (old_hitAngle != hitAngle):
                as_event('ON_CALC_ARMOR')
            return _SHOT_RESULT.UNDEFINED
        player = BigWorld.player()
        if player is None:
            if (old_armorActual != armorActual) or (old_piercingActual != piercingActual) or (old_hitAngle != hitAngle):
                as_event('ON_CALC_ARMOR')
            return _SHOT_RESULT.UNDEFINED
        vDesc = player.getVehicleDescriptor()
        shell = vDesc.shot.shell
        caliber = shell.caliber
        shellKind = shell.kind
        ppDesc = vDesc.shot.piercingPower
        maxDist = vDesc.shot.maxDistance
        dist = (hitPoint - player.getOwnVehiclePosition()).length
        piercingPower = cls._computePiercingPowerAtDist(ppDesc, dist, maxDist, piercingMultiplier)
        fullPiercingPower = piercingPower
        minPP, maxPP = cls._computePiercingPowerRandomization(shell)
        result = _SHOT_RESULT.NOT_PIERCED
        isJet = False
        jetStartDist = None
        ignoredMaterials = set()
        collisionsDetails = cls._getAllCollisionDetails(hitPoint, direction, entity)
        if collisionsDetails is None:
            if (old_armorActual != armorActual) or (old_piercingActual != piercingActual) or (old_hitAngle != hitAngle):
                as_event('ON_CALC_ARMOR')
            return _SHOT_RESULT.UNDEFINED
        for cDetails in collisionsDetails:
            if isJet:
                jetDist = cDetails.dist - jetStartDist
                if jetDist > 0.0:
                    piercingPower *= 1.0 - jetDist * cls._SHELL_EXTRA_DATA[shellKind].jetLossPPByDist
            if cDetails.matInfo is None:
                result = cls._CRIT_ONLY_SHOT_RESULT
            else:
                matInfo = cDetails.matInfo
                if (cDetails.compName, matInfo.kind) in ignoredMaterials:
                    continue
                hitAngleCos = cDetails.hitAngleCos if matInfo.useHitAngle else 1.0
                hitAngle = hitAngleCos
                normHitAngle = hitAngle
                if not isJet and cls._shouldRicochet(shellKind, hitAngleCos, matInfo, caliber):
                    normHitAngle = -1.0
                    break
                piercingPercent = 1000.0
                if piercingPower > 0.0:
                    penetrationArmor = cls._computePenetrationArmor(shellKind, hitAngleCos, matInfo, caliber)
                    normHitAngle = matInfo.armor / penetrationArmor if penetrationArmor != 0.0 else hitAngle
                    piercingPercent = 100.0 + (penetrationArmor - piercingPower) / fullPiercingPower * 100.0
                    piercingActual = int(piercingPower)
                    armorActual = int(penetrationArmor)
                    # piercingChance = max(0, min(1.0, (piercingPower / penetrationArmor - 0.75) * 2)) if penetrationArmor > 0.0 else 1.0
                    armorRatio = penetrationArmor / piercingPower - 1.0
                    # piercingChance = 1.0 if armorRatio < -0.25 else 0.5 * math.erfc(8.485281374238576 * armorRatio) if armorRatio <= 0.25 else 0.0
                    if armorRatio < -0.25:
                        piercingChance = 1.0
                    elif armorRatio > 0.25:
                        piercingChance = 0.0
                    else:
                        piercingChance = 0.5 * math.erfc(8.485281374238576 * armorRatio)
                    piercingPower -= penetrationArmor
                    # log('penetrationArmor = %s     piercingPercent = %s    piercingPower = %s' % (penetrationArmor, piercingPercent, piercingPower))
                if matInfo.vehicleDamageFactor:
                    if minPP < piercingPercent < maxPP:
                        result = _SHOT_RESULT.LITTLE_PIERCED
                    elif piercingPercent <= minPP:
                        result = _SHOT_RESULT.GREAT_PIERCED
                    break
                elif matInfo.extra:
                    if piercingPercent <= maxPP:
                        result = cls._CRIT_ONLY_SHOT_RESULT
                if matInfo.collideOnceOnly:
                    ignoredMaterials.add((cDetails.compName, matInfo.kind))
            if piercingPower <= 0.0:
                break
            if cls._SHELL_EXTRA_DATA[shellKind].jetLossPPByDist > 0.0:
                isJet = True
                mInfo = cDetails.matInfo
                armor = mInfo.armor if mInfo is not None else 0.0
                jetStartDist = cDetails.dist + armor * 0.001
        shotResult = PIERCING_CHANCE_KEY[result]
        if (old_armorActual != armorActual) or (old_piercingActual != piercingActual) or (old_hitAngle != hitAngle):
            as_event('ON_CALC_ARMOR')
        return result
    else:
        return base(hitPoint, collision, direction, excludeTeam)


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global piercingActual, armorActual, shotResult, hitAngle, normHitAngle, colorPiercingChance, piercingChance, visible
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        piercingActual = None
        armorActual = None
        piercingChance = None
        shotResult = None
        hitAngle = None
        normHitAngle = None
        visible = True
        colorPiercingChance = config.get('sight/c_piercingChance', COLOR_PIERCING_CHANCE)
        as_event('ON_CALC_ARMOR')


@registerEvent(PlayerAvatar, 'updateVehicleHealth')
def PlayerAvatar_updateVehicleHealth(self, vehicleID, health, deathReasonID, isCrewActive, isRespawn):
    if not (health > 0 and isCrewActive) and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global piercingActual, armorActual, shotResult, hitAngle, normHitAngle, colorPiercingChance, piercingChance
        piercingActual = None
        armorActual = None
        piercingChance = None
        shotResult = None
        hitAngle = None
        normHitAngle = None
        as_event('ON_CALC_ARMOR')


@xvm.export('sight.piercingActual', deterministic=False)
def sight_piercingActual():
    return piercingActual if visible else None


@xvm.export('sight.hitAngle', deterministic=False)
def sight_hitAngle():
    return math.degrees(math.acos(hitAngle)) if hitAngle is not None and visible else None


@xvm.export('sight.normHitAngle', deterministic=False)
def sight_normHitAngel():
    if visible:
        return normHitAngle if (normHitAngle is None) or (normHitAngle < 0) else math.degrees(math.acos(normHitAngle))


@xvm.export('sight.armorActual', deterministic=False)
def sight_piercingActual():
    return armorActual if visible else None


@xvm.export('sight.c_piercingChance', deterministic=False)
def sight_c_piercingChance():
    return colorPiercingChance.get(shotResult, colorPiercingChance.get(NOT_TARGET, None))


@xvm.export('sight.piercingChanceKey', deterministic=False)
def sight_piercingChanceKey():
    if visible:
        return shotResult if shotResult is not None else NOT_TARGET


@xvm.export('sight.piercingChance', deterministic=False)
def sight_piercingChance(norm=None):
    global piercingChance
    if not visible:
        return None
    if piercingChance is not None:
        piercingChance = (piercingChance * 100 if norm is None else piercingChance * norm)
    return piercingChance
