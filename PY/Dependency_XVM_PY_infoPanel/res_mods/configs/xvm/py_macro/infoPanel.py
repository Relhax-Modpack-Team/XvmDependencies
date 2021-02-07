from BigWorld import player, target
from Avatar import PlayerAvatar
from gui.shared.utils.TimeInterval import TimeInterval
from messenger import MessengerEntry
from xfw import overrideMethod, registerEvent
from xfw_actionscript.python import as_event
from xvm import info_panel_data
from xvm_main.python import config
from xvm_main.python.xvm import l10n

infoPanelConfig = config.get('infoPanel', {'enabled': False, 'showFor': 'all', 'aliveOnly': False, 'altKey': None})

MACROS = [
    '{{nick_name}}', '{{marks_on_gun}}', '{{vehicle_type}}', '{{vehicle_name}}', '{{vehicle_system_name}}', '{{icon_system_name}}', '{{gun_name}}', '{{gun_caliber}}',
    '{{max_ammo}}', '{{gun_reload}}', '{{gun_dpm}}', '{{gun_reload_equip}}', '{{gun_dpm_equip}}', '{{gun_clip}}', '{{gun_clip_reload}}',
    '{{gun_burst}}', '{{gun_burst_reload}}', '{{gun_aiming_time}}', '{{gun_accuracy}}', '{{shell_name_1}}', '{{shell_name_2}}', '{{shell_name_3}}',
    '{{shell_damage_1}}', '{{shell_damage_2}}', '{{shell_damage_3}}', '{{shell_power_1}}', '{{shell_power_2}}', '{{shell_power_3}}', '{{shell_type_1}}',
    '{{shell_type_2}}', '{{shell_type_3}}', '{{shell_speed_1}}', '{{shell_speed_2}}', '{{shell_speed_3}}', '{{shell_distance_1}}', '{{shell_distance_2}}',
    '{{shell_distance_3}}', '{{angle_pitch_up}}', '{{angle_pitch_down}}', '{{angle_pitch_left}}', '{{angle_pitch_right}}', '{{vehicle_max_health}}',
    '{{armor_hull_front}}', '{{armor_hull_side}}', '{{armor_hull_back}}', '{{turret_name}}', '{{armor_turret_front}}', '{{armor_turret_side}}',
    '{{armor_turret_back}}', '{{vehicle_weight}}', '{{chassis_max_weight}}', '{{engine_name}}', '{{engine_power}}', '{{engine_power_density}}', 
    '{{speed_forward}}', '{{speed_backward}}', '{{hull_speed_turn}}', '{{turret_speed_turn}}', '{{invis_stand}}', '{{invis_stand_shot}}', '{{invis_move}}', 
    '{{invis_move_shot}}', '{{vision_radius}}', '{{radio_name}}', '{{radio_radius}}',
    '{{nation}}', '{{level}}', '{{rlevel}}',
    #
    '{{pl_vehicle_weight}}', '{{pl_gun_reload}}', '{{pl_gun_reload_equip}}', '{{pl_gun_dpm}}', '{{pl_gun_dpm_equip}}', '{{pl_vision_radius}}',
    '{{pl_gun_aiming_time}}'
]

###

def _getL10n(text):
    if text.find('{{l10n:') > -1:
        return l10n(text)
    return text

def _isEntitySatisfiesConditions(entity):
    if (entity is None) or not hasattr(entity, 'publicInfo'):
        return False
    isAlly = 0 < getattr(entity.publicInfo, 'team', 0) == player().team
    showFor = (infoPanelConfig['showFor'] == 'all') or ((infoPanelConfig['showFor'] == 'ally') and isAlly) or ((infoPanelConfig['showFor'] == 'enemy') and not isAlly)
    aliveOnly = (not infoPanelConfig['aliveOnly']) or (infoPanelConfig['aliveOnly'] and entity.isAlive())
    return showFor and aliveOnly

###

class infoPanel(object):

    def __init__(self):
        self.textFormats = infoPanelConfig['formats'] if infoPanelConfig['enabled'] else None
        self.textsFormatted = None
        self.timer = None
        self.hotKeyDown = False
        self.visible = False

    def reset(self):
        self.__init__()
        info_panel_data.reset()

    def getFuncResponse(self, funcName):
        if not hasattr(info_panel_data, funcName):
            return None
        func = getattr(info_panel_data, funcName, None)
        if (func is not None) and callable(func):
            result = func()
            return str(result) if result is not None else ''
        else:
            return None

    def setTextsFormatted(self):
        self.textsFormatted = []
        for textFormat in self.textFormats:
            for macro in MACROS:
                if macro in textFormat:
                    funcName = macro.replace('{', '').replace('}', '')
                    funcResponse = self.getFuncResponse(funcName)
                    textFormat = textFormat.replace(macro, funcResponse)
            self.textsFormatted.append(_getL10n(textFormat))

    def handleKey(self, isDown):
        if isDown:
            self.update(player().getVehicleAttached())
            self.hotKeyDown = True
        elif not isDown:
            self.hotKeyDown = False
            _target = target()
            if _isEntitySatisfiesConditions(_target):
                self.update(_target)
            else:
                self.hide()

    def hide(self):
        if self.timer is not None and self.timer.isStarted():
            self.timer.stop()
            self.timer = None
        self.textsFormatted = None
        self.visible = False
        as_event('ON_INFO_PANEL')

    def updateBlur(self):
        if self.hotKeyDown or (player().getVehicleAttached() is None):
            return
        if self.timer is not None and self.timer.isStarted():
            self.timer.stop()
            self.timer = None
        self.timer = TimeInterval(infoPanelConfig['delay'], self, 'hide')
        self.timer.start()

    def update(self, vehicle):
        if self.hotKeyDown:
            return
        playerVehicle = player().getVehicleAttached()
        if playerVehicle is not None:
            self.visible = True
            if hasattr(vehicle, 'typeDescriptor'):
                info_panel_data.init(vehicle, playerVehicle)
            elif hasattr(playerVehicle, 'typeDescriptor'):
                info_panel_data.init(None, playerVehicle)
            self.setTextsFormatted()
            as_event('ON_INFO_PANEL')

infoPanel = infoPanel()

###

@overrideMethod(PlayerAvatar, 'targetBlur')
def targetBlur(base, self, prevEntity):
    if infoPanelConfig['enabled'] and _isEntitySatisfiesConditions(prevEntity):
        infoPanel.updateBlur()
    base(self, prevEntity) 

@registerEvent(PlayerAvatar, 'targetFocus')
def targetFocus(self, entity):
    if infoPanelConfig['enabled'] and _isEntitySatisfiesConditions(entity):
        infoPanel.update(entity)

@registerEvent(PlayerAvatar, 'handleKey')
def handleKey(self, isDown, key, mods):
    if not infoPanelConfig['enabled'] or (key != infoPanelConfig['altKey']) or MessengerEntry.g_instance.gui.isFocused():
        return
    infoPanel.handleKey(isDown)

@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def _PlayerAvatar__destroyGUI(self):
    if not infoPanelConfig['enabled']:
        return
    infoPanel.reset()

###

@xvm.export('infoPanel.format', deterministic=False)
def infoPanelFormat(idx = 0):
    if (infoPanel.textsFormatted is not None) and (idx < len(infoPanel.textsFormatted)):
        return infoPanel.textsFormatted[idx]

#

@xvm.export('infoPanel.isVisible', deterministic=False)
def isVisible():
    return 'visible' if infoPanel.visible else ''

@xvm.export('infoPanel.isTarget', deterministic=False)
def isTarget():
    return '' if ((target() is None) or infoPanel.hotKeyDown) else 'trg'

@xvm.export('infoPanel.isPremium', deterministic=False)
def isPremium():
    _typeDescriptor = player().getVehicleAttached().typeDescriptor if ((target() is None) or infoPanel.hotKeyDown) else target().typeDescriptor
    return 'premium' if ('premium' in _typeDescriptor.type.tags) else ''

@xvm.export('infoPanel.compareDelim', deterministic=False)
def compareDelim(value1, value2):
    if value1 > value2:
        return infoPanelConfig['compareValues']['moreThan']['delim']
    elif value1 == value2:
        return infoPanelConfig['compareValues']['equal']['delim']
    elif value1 < value2:
        return infoPanelConfig['compareValues']['lessThan']['delim']

@xvm.export('infoPanel.compareColor', deterministic=False)
def compareColor(value1, value2):
    if value1 > value2:
        return infoPanelConfig['compareValues']['moreThan']['color']
    elif value1 == value2:
        return infoPanelConfig['compareValues']['equal']['color']
    elif value1 < value2:
        return infoPanelConfig['compareValues']['lessThan']['color']
