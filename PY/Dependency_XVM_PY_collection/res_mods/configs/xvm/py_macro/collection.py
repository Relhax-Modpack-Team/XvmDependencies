import BigWorld
import cPickle
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from items import vehicles
from ClientArena import ClientArena

from xvm_main.python.logger import *
from xfw.events import registerEvent


deadPlayer = {}
players = {}
_vehicles = None


def update(vehicle):
    global players

    vehType = vehicle['vehicleType']
    gun = vehType.gun
    _miscAttrs = vehType.miscAttrs
    reloadVehicle = gun.reloadTime * _miscAttrs.get('gunReloadTimeFactor', 1) / (1.0695 + 0.0043 * _miscAttrs.get('crewLevelIncrease', 0))
    circularVisionRadius = vehType.turret.circularVisionRadius * _miscAttrs.get('circularVisionRadiusFactor', 1)
    piercingPower = [shot.piercingPower[0] for shot in gun.shots]
    damage = [shot.shell.damage[0] for shot in gun.shots]
    players[vehicle['name']] = {'reloadVehicle': reloadVehicle,
                                'circularVisionRadius': circularVisionRadius,
                                'damage': damage[0],
                                'piercingPower': piercingPower[0]}


@registerEvent(PlayerAvatar, 'onEnterWorld')
def PlayerAvatar_onEnterWorld(self, prereqs):
    global deadPlayer, players, _vehicles
    deadPlayer = {}
    players = {}
    _vehicles = self.arena.vehicles
    for vehicle in _vehicles.itervalues():
        update(vehicle)


@registerEvent(Vehicle, 'onHealthChanged', True)
def onHealthChanged(self, newHealth, attackerID, attackReasonID):
    global deadPlayer, _vehicles
    if self.isAlive():
        return
    if attackerID not in _vehicles:
        _vehicles = BigWorld.player().arena.vehicles
    attacker = _vehicles.get(attackerID, None)
    target = _vehicles.get(self.id, None)
    if attacker is not None:
        shortUserString = attacker['vehicleType'].type.shortUserString if attacker['vehicleType'] is not None else ''
        name = attacker['name'] if 'name' in attacker else ''
        deadPlayer[target['name']] = {'attackerName': name, 'attackerVehicle': shortUserString}
    else:
        deadPlayer[target['name']] = {'attackerName': '', 'attackerVehicle': ''}


def updatePlayer(name):
    vehicles = BigWorld.player().arena.vehicles
    for vehicle in vehicles.itervalues():
        if vehicle['name'] == name:
            update(vehicle)
            break


@xvm.export('killerName', deterministic=False)
def killerName(name):
    return deadPlayer[name].get('attackerName', None) if name in deadPlayer else None


@xvm.export('killerVehicle', deterministic=False)
def killerVehicle(name):
    return deadPlayer[name].get('attackerVehicle', None) if name in deadPlayer else None


@xvm.export('reloadVehicle')
def reloadVehicle(name):
    if name not in players:
        updatePlayer(name)
    return players[name].get('reloadVehicle', None) if name in players else None


@xvm.export('visionRadius')
def visionRadius(name):
    if name not in players:
        updatePlayer(name)
    return players[name].get('circularVisionRadius', None) if name in players else None


@xvm.export('piercingPower')
def piercingPower(name):
    if name not in players:
        updatePlayer(name)
    return players[name].get('piercingPower', None) if name in players else None


@xvm.export('shellDamage')
def shellDamage(name):
    if name not in players:
        updatePlayer(name)
    return players[name].get('damage', None) if name in players else None
