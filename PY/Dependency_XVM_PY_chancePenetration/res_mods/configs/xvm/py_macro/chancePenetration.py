import BigWorld
import math
from Vehicle import Vehicle
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from AvatarInputHandler.gun_marker_ctrl import _CrosshairShotResults, _SHOT_RESULT
import gui.Scaleform.daapi.view.battle.shared.crosshair.plugins as plug
from math import erfc

from xfw import *
from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle


COLOR_PIERCING_CHANCE = {'not_pierced':    '#E82929',
                         'little_pierced': '#E1C300',
                         'great_pierced':  '#2ED12F',
                         'not_target':     ''}

piercingActual = None
armorActual = None
piercingChance = None
shotResult = None
hitAngle = None
normHitAngle = None
colorPiercingChance = COLOR_PIERCING_CHANCE
playerVehicleID = None


@registerEvent(plug.ShotResultIndicatorPlugin, '_ShotResultIndicatorPlugin__onGunMarkerStateChanged')
def onGunMarkerStateChanged(self, markerType, position, dir, collision):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        if not self._ShotResultIndicatorPlugin__isEnabled:
             self._ShotResultIndicatorPlugin__shotResultResolver.getShotResult(position, collision, dir, excludeTeam=self._ShotResultIndicatorPlugin__playerTeam)


@overrideClassMethod(_CrosshairShotResults, 'getShotResult')
def _CrosshairShotResults_getShotResult(base, cls, hitPoint, collision, dir, excludeTeam=0):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        def updateLabel():
            if (old_armorActual != armorActual) or (old_piercingActual != piercingActual):
                as_event('ON_CALC_ARMOR')

        global piercingActual, armorActual, shotResult, hitAngle, normHitAngle, piercingChance
        keyColor = [None, 'not_pierced', 'little_pierced', 'great_pierced']
        old_piercingActual = piercingActual
        old_armorActual = armorActual
        piercingActual = None
        armorActual = None
        piercingChance = None
        hitAngle = None
        normHitAngle = None
        shotResult = keyColor[0]
        if collision is None:
            updateLabel()
            return _SHOT_RESULT.UNDEFINED
        else:
            entity = collision.entity
            if entity.__class__.__name__ not in ('Vehicle', 'DestructibleEntity'):
                updateLabel()
                return _SHOT_RESULT.UNDEFINED
            if entity.health <= 0 or entity.publicInfo['team'] == excludeTeam:
                updateLabel()
                return _SHOT_RESULT.UNDEFINED
            player = BigWorld.player()
            if player is None:
                updateLabel()
                return _SHOT_RESULT.UNDEFINED
            vDesc = player.getVehicleDescriptor()
            shell = vDesc.shot.shell
            caliber = shell.caliber
            shellKind = shell.kind
            ppDesc = vDesc.shot.piercingPower
            maxDist = vDesc.shot.maxDistance
            dist = (hitPoint - player.getOwnVehiclePosition()).length
            piercingPower = cls._computePiercingPowerAtDist(ppDesc, dist, maxDist)
            fullPiercingPower = piercingPower
            minPP, maxPP = cls._computePiercingPowerRandomization(shell)
            result = _SHOT_RESULT.NOT_PIERCED
            isJet = False
            jetStartDist = None
            ignoredMaterials = set()
            collisionsDetails = cls._getAllCollisionDetails(hitPoint, dir, entity)
            if collisionsDetails is None:
                updateLabel()
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
                        armorRatio = float(penetrationArmor) / piercingPower - 1
                        piercingChance = 1.0 if armorRatio < -0.25 else 0.5 * erfc(8.485281374238576 * armorRatio ) if armorRatio <= 0.25 else 0.0
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
            shotResult = keyColor[result]
            updateLabel()
            return result
    else:
        return base(hitPoint, collision, dir, excludeTeam)


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global piercingActual, armorActual, shotResult, hitAngle, normHitAngle, colorPiercingChance, playerVehicleID, piercingChance
    if self.isPlayerVehicle and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        piercingActual = None
        armorActual = None
        piercingChance = None
        shotResult = None
        hitAngle = None
        normHitAngle = None
        colorPiercingChance = config.get('sight/c_piercingChance', COLOR_PIERCING_CHANCE)
        playerVehicleID = self.id
        as_event('ON_CALC_ARMOR')


@registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
    global piercingActual, armorActual, shotResult, hitAngle, normHitAngle, colorPiercingChance, piercingChance
    if (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID) and battle.isBattleTypeSupported:
        piercingActual = None
        armorActual = None
        piercingChance = None
        shotResult = None
        hitAngle = None
        normHitAngle = None
        as_event('ON_CALC_ARMOR')


@xvm.export('sight.piercingActual', deterministic=False)
def sight_piercingActual():
    return piercingActual


@xvm.export('sight.hitAngle', deterministic=False)
def sight_hitAngle():
    return math.degrees(math.acos(hitAngle)) if hitAngle is not None else None


@xvm.export('sight.normHitAngle', deterministic=False)
def sight_normHitAngel():
    return normHitAngle if (normHitAngle is None) or (normHitAngle < 0) else math.degrees(math.acos(normHitAngle))


@xvm.export('sight.armorActual', deterministic=False)
def sight_piercingActual():
    return armorActual


@xvm.export('sight.c_piercingChance', deterministic=False)
def sight_c_piercingChance():
    return colorPiercingChance.get(shotResult, colorPiercingChance.get('not_target', None))


@xvm.export('sight.piercingChance', deterministic=False)
def sight_piercingChance(norm=None):
    global piercingChance
    if piercingChance is not None:
        piercingChance = (piercingChance * 100 if norm is None else piercingChance * norm)
    return piercingChance
