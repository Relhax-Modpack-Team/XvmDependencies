from nations import NAMES
from xvm_main.python.xvm import l10n
from math import degrees

#####################################################################
# private

_playerVehicle = None
_vehicle = None
_typeDescriptor = None
_gunShots = None

def init(vehicle, playerVehicle = None):
    global _playerVehicle, _vehicle, _typeDescriptor, _gunShots
    _playerVehicle = playerVehicle
    _vehicle = vehicle
    _typeDescriptor = vehicle.typeDescriptor if vehicle is not None else _playerVehicle.typeDescriptor
    _gunShots = _typeDescriptor.gun.shots

def reset():
    global _playerVehicle, _vehicle, _typeDescriptor, _gunShots
    _playerVehicle = None
    _vehicle = None
    _typeDescriptor = None
    _gunShots = None

#####################################################################
# handlers

def nick_name():
    return None if not _vehicle else "%s" % (_vehicle.publicInfo.name)

def marks_on_gun():
    return None if not _vehicle else "%s" % (_vehicle.publicInfo.marksOnGun)

def vehicle_type():
    vehType = None
    if _typeDescriptor is not None and 'lightTank' in _typeDescriptor.type.tags: 
        vehType = 'LT'
    elif _typeDescriptor is not None and 'mediumTank' in _typeDescriptor.type.tags:
        vehType = 'MT'
    elif _typeDescriptor is not None and 'heavyTank' in _typeDescriptor.type.tags:
        vehType = 'HT'
    elif _typeDescriptor is not None and 'AT-SPG' in _typeDescriptor.type.tags:
        vehType = 'TD'
    elif _typeDescriptor is not None and 'SPG' in _typeDescriptor.type.tags:
        vehType = 'SPG'        
    return l10n(vehType)

def vehicle_name():
    return None if not _typeDescriptor else "%s" % (_typeDescriptor.type.userString)

def vehicle_system_name():
    return None if not _typeDescriptor else "%s" % (_typeDescriptor.name)

def icon_system_name():
    return None if not _typeDescriptor else "%s" % (_typeDescriptor.name.replace(':', '-'))

def gun_name():
    return None if not _typeDescriptor else "%s" % (_typeDescriptor.gun.shortUserString)

def gun_caliber():
    return None if not gs else "%d" % (gs[0].shell.caliber)

def max_ammo():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.gun.maxAmmo)

def gun_reload():
    return None if not _typeDescriptor else "%.2f" % (_typeDescriptor.gun.reloadTime)

def gun_dpm():
    if not _typeDescriptor: 
        return None
    else:
        time = _typeDescriptor.gun.reloadTime + (_typeDescriptor.gun.clip[0] - 1) * _typeDescriptor.gun.clip[1]
        return "%d" % (round(_typeDescriptor.gun.clip[0] / time * 60 * _typeDescriptor.gun.shots[0].shell.damage[0], 0))

def gun_reload_equip(eq1 = 1, eq2 = 1, eq3 = 1, eq4 = 1):
    if not _typeDescriptor: 
        return None
    else:
        reload_orig = _typeDescriptor.gun.reloadTime
        rammer = 0.9 if (_typeDescriptor.gun.clip[0] == 1) and (eq1 == 1) else 1
        if (eq2 == 1) and (eq3 == 1) and (eq4 == 1):
            crew = 1.32
        elif (eq2 == 1) and (eq3 == 1) and (eq4 == 0):
            crew = 1.27
        elif (eq2 == 1) and (eq3 == 0) and (eq4 == 1):
            crew = 1.21
        elif (eq2 == 1) and (eq3 == 0) and (eq4 == 0):
            crew = 1.16
        elif (eq2 == 0) and (eq3 == 1) and (eq4 == 1):
            crew = 1.27
        elif (eq2 == 0) and (eq3 == 1) and (eq4 == 0):
            crew = 1.21
        elif (eq2 == 0) and (eq3 == 0) and (eq4 == 1):
            crew = 1.16
        else:
            crew = 1.10
        return "%.2f" % (round((reload_orig / (0.57 + 0.43 * crew)) * rammer, 2))

def gun_dpm_equip(eq1 = 1, eq2 = 1, eq3 = 1, eq4 = 1):
    if not _typeDescriptor: 
        return None
    else:
        reload_equip = float(gun_reload_equip(eq1, eq2, eq3, eq4))
        time = reload_equip + (_typeDescriptor.gun.clip[0] - 1) * _typeDescriptor.gun.clip[1]
        return "%d" % (round(_typeDescriptor.gun.clip[0] / time * 60 * _typeDescriptor.gun.shots[0].shell.damage[0], 0))

def gun_clip():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.gun.clip[0])

def gun_clip_reload():
    return None if not _typeDescriptor else "%.1f" % (_typeDescriptor.gun.clip[1])

def gun_burst():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.gun.burst[0])

def gun_burst_reload():
    return None if not _typeDescriptor else "%.1f" % (_typeDescriptor.gun.burst[1])    

def gun_aiming_time():
    return None if not _typeDescriptor else "%.1f" % (_typeDescriptor.gun.aimingTime)

def gun_accuracy():
    return None if not _typeDescriptor else "%.2f" % round(_typeDescriptor.gun.shotDispersionAngle * 100, 2)

def shell_name_1():
    return None if (not _gunShots) or (len(_gunShots) < 1) else "%s" % (_gunShots[0].shell.userString)

def shell_name_2():
    return None if (not _gunShots) or (len(_gunShots) < 2) else "%s" % (_gunShots[1].shell.userString)

def shell_name_3():
    return None if (not _gunShots) or (len(_gunShots) < 3) else "%s" % (_gunShots[2].shell.userString)

def shell_damage_1():
    return None if (not _gunShots) or (len(_gunShots) < 1) else "%d" % (_gunShots[0].shell.damage[0])

def shell_damage_2():
    return None if (not _gunShots) or (len(_gunShots) < 2) else "%d" % (_gunShots[1].shell.damage[0])

def shell_damage_3():
    return None if (not _gunShots) or (len(_gunShots) < 3) else "%d" % (_gunShots[2].shell.damage[0])

def shell_power_1():
    return None if (not _gunShots) or (len(_gunShots) < 1) else "%d" % (_gunShots[0].piercingPower[0])

def shell_power_2():
    return None if (not _gunShots) or (len(_gunShots) < 2) else "%d" % (_gunShots[1].piercingPower[0])

def shell_power_3():
    return None if (not _gunShots) or (len(_gunShots) < 3) else "%d" % (_gunShots[2].piercingPower[0])

def shell_type_1():
    return None if (not _gunShots) or (len(_gunShots) < 1) else l10n(_gunShots[0].shell.kind.lower())

def shell_type_2():
    return None if (not _gunShots) or (len(_gunShots) < 2) else l10n(_gunShots[1].shell.kind.lower())

def shell_type_3():
    return None if (not _gunShots) or (len(_gunShots) < 3) else l10n(_gunShots[2].shell.kind.lower())

def shell_speed_1():
    return None if (not _gunShots) or (len(_gunShots) < 1) else "%d" % round(_gunShots[0].speed * 1.25)

def shell_speed_2():
    return None if (not _gunShots) or (len(_gunShots) < 2) else "%d" % round(_gunShots[1].speed * 1.25)

def shell_speed_3():
    return None if (not _gunShots) or (len(_gunShots) < 3) else "%d" % round(_gunShots[2].speed * 1.25)

def shell_distance_1():
    return None if (not _gunShots) or (len(_gunShots) < 1) else "%d" % (_gunShots[0].maxDistance)

def shell_distance_2():
    return None if (not _gunShots) or (len(_gunShots) < 2) else "%d" % (_gunShots[1].maxDistance)

def shell_distance_3():
    return None if (not _gunShots) or (len(_gunShots) < 3) else "%d" % (_gunShots[2].maxDistance)

def stun_radius():
    if (_gunShots is not None) and (_gunShots[0].shell.stun is not None):
        return "%d" % (_gunShots[0].shell.stun.stunRadius)
    else:
        return None

def stun_duration_min():
    if (_gunShots is not None) and (_gunShots[0].shell.stun is not None):
        time = (round(_gunShots[0].shell.stun.stunRadius * _gunShots[0].shell.stun.guaranteedStunDuration, 1))
        return "%.1f" % (time)
    else:
        return None

def stun_duration_max():
    if (_gunShots is not None) and (_gunShots[0].shell.stun is not None):
        return "%d" % (_gunShots[0].shell.stun.stunDuration)
    else:
        return None

def angle_pitch_up():
    return None if not _typeDescriptor else "%d" % (degrees(-_typeDescriptor.gun.pitchLimits['absolute'][0]))

def angle_pitch_down():
    return None if not _typeDescriptor else "%d" % (degrees(-_typeDescriptor.gun.pitchLimits['absolute'][1]))

def angle_pitch_left():
    return None if (not _typeDescriptor) or (not _typeDescriptor.gun.turretYawLimits) else "%d" % (degrees(-_typeDescriptor.gun.turretYawLimits[0]))

def angle_pitch_right():
    return None if (not _typeDescriptor) or (not _typeDescriptor.gun.turretYawLimits) else "%d" % (degrees(_typeDescriptor.gun.turretYawLimits[1]))

def vehicle_max_health():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.maxHealth)

def armor_hull_front():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.hull.primaryArmor[0])

def armor_hull_side():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.hull.primaryArmor[1])

def armor_hull_back():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.hull.primaryArmor[2])

def turret_name():
    return None if not _typeDescriptor else "%s" % (_typeDescriptor.turret.shortUserString)

def armor_turret_front():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.turret.primaryArmor[0])

def armor_turret_side():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.turret.primaryArmor[1])

def armor_turret_back():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.turret.primaryArmor[2])

def vehicle_weight():
    return None if not _typeDescriptor else "%.1f" % (round(_typeDescriptor.physics['weight'] / 1000, 1))

def chassis_max_weight():
    return None if not _typeDescriptor else "%.1f" % (round(_typeDescriptor.chassis.maxLoad / 1000, 1))

def engine_name():
    return None if not _typeDescriptor else "%s" % (_typeDescriptor.engine.shortUserString)

def engine_power():
    return None if not _typeDescriptor else "%d" % (round(_typeDescriptor.engine.power / 735.49875, 0))

def engine_power_density():
    if not _typeDescriptor: 
        return None
    else:
        power = _typeDescriptor.engine.power / 735.49875
        weight = _typeDescriptor.physics['weight'] / 1000
        return "%.2f" % (round(power / weight, 2))

def speed_forward():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.physics['speedLimits'][0] * 3.6)

def speed_backward():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.physics['speedLimits'][1] * 3.6)

def hull_speed_turn():
    return None if not _typeDescriptor else "%.2f" % (degrees(_typeDescriptor.chassis.rotationSpeed))

def turret_speed_turn():
    return None if not _typeDescriptor else "%.2f" % (degrees(_typeDescriptor.turret.rotationSpeed))

def invis_stand():
    return None if not _typeDescriptor else "%.1f" % (_typeDescriptor.type.invisibility[1] * 57)

def invis_stand_shot():
    return None if not _typeDescriptor else "%.2f" % (_typeDescriptor.type.invisibility[1] * _typeDescriptor.gun.invisibilityFactorAtShot * 57)

def invis_move():
    return None if not _typeDescriptor else "%.1f" % (_typeDescriptor.type.invisibility[0] * 57)

def invis_move_shot():
    return None if not _typeDescriptor else "%.2f" % (_typeDescriptor.type.invisibility[0] * _typeDescriptor.gun.invisibilityFactorAtShot * 57)

def vision_radius():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.turret.circularVisionRadius)

def radio_name():
    return None if not _typeDescriptor else "%s" % (_typeDescriptor.radio.shortUserString)

def radio_radius():
    return None if not _typeDescriptor else "%d" % (_typeDescriptor.radio.distance)

def nation():
    return None if not _typeDescriptor else l10n(NAMES[_typeDescriptor.type.customizationNationID])

def level():
    return None if not _typeDescriptor else "%d" % _typeDescriptor.type.level

def rlevel():
    _ROMAN_LEVEL = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X')
    return None if not _typeDescriptor else _ROMAN_LEVEL[_typeDescriptor.type.level - 1]

#####################################################################
# Player only

def pl_gun_reload():
    global _typeDescriptor
    _typeDescriptor = _playerVehicle.typeDescriptor
    return gun_reload()

def pl_gun_reload_equip():
    global _typeDescriptor
    _typeDescriptor = _playerVehicle.typeDescriptor
    return gun_reload_equip()

def pl_gun_dpm():
    global _typeDescriptor
    _typeDescriptor = _playerVehicle.typeDescriptor
    return gun_dpm()

def pl_gun_dpm_equip():
    global _typeDescriptor
    _typeDescriptor = _playerVehicle.typeDescriptor
    return gun_dpm_equip()

def pl_vehicle_weight():
    global _typeDescriptor
    _typeDescriptor = _playerVehicle.typeDescriptor
    return vehicle_weight()

def pl_vision_radius():
    global _typeDescriptor
    _typeDescriptor = _playerVehicle.typeDescriptor
    return vision_radius()

def pl_gun_aiming_time():
    global _typeDescriptor
    _typeDescriptor = _playerVehicle.typeDescriptor
    return gun_aiming_time()
