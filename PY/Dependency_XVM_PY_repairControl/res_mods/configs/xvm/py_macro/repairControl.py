import Keys
from BigWorld import player
from Vehicle import Vehicle
from Avatar import PlayerAvatar
from AvatarInputHandler import AvatarInputHandler
from helpers import dependency
from aih_constants import CTRL_MODE_NAME
from skeletons.gui.battle_session import IBattleSessionProvider
from gui.battle_control.avatar_getter import isVehicleInFire
from gui.battle_control.battle_constants import VEHICLE_COMPLEX_ITEMS, VEHICLE_DEVICE_IN_COMPLEX_ITEM, VEHICLE_GUI_ITEMS
from gui.Scaleform.daapi.view.battle.shared.damage_panel import DamagePanel
from xfw import registerEvent
from xfw_actionscript.python import as_event, as_callback

###

ENGINE     = 'engine'
AMMOBAY    = 'ammoBay'
GUN        = 'gun'
TURRET     = 'turretRotator'
SURVEYING  = 'surveyingDevice'
RADIO      = 'radio'
FUELTANK   = 'fuelTank'
COMPLEX    = 'complex' #custom alias for chassis and wheels
LEFTTRACK  = 'leftTrack'
RIGHTTRACK = 'rightTrack'
WHEEL0     = 'wheel0'
WHEEL1     = 'wheel1'
WHEEL2     = 'wheel2'
WHEEL3     = 'wheel3'
WHEEL4     = 'wheel4'
WHEEL5     = 'wheel5'
WHEEL6     = 'wheel6'
WHEEL7     = 'wheel7'

#complex types
CHASSIS = 'chassis' #custom
WHEEL   = 'wheel'   #custom

COMMANDER = 'commander'
RADIOMAN  = 'radioman'
DRIVER    = 'driver'
GUNNER    = 'gunner'
LOADER    = 'loader'

DEVICES = frozenset([
    ENGINE, AMMOBAY, GUN, TURRET, SURVEYING, RADIO, FUELTANK,
    COMPLEX,
    LEFTTRACK, RIGHTTRACK,
    WHEEL0, WHEEL1, WHEEL2, WHEEL3, WHEEL4, WHEEL5, WHEEL6, WHEEL7
])

CREW = frozenset([
    COMMANDER, RADIOMAN, DRIVER, GUNNER, LOADER
])

EVENTABLE_ITEMS = frozenset([
    ENGINE, AMMOBAY, GUN, TURRET, COMPLEX, SURVEYING, RADIO, FUELTANK,
    COMMANDER, RADIOMAN, DRIVER, GUNNER, LOADER
])

REPAIR_ITEMS = {
    'extinguisher': 251,
    'med_kit':      763,
    'g_med_kit':    1019,
    'repair_kit':   1275,
    'g_repair_kit': 1531
}

PREFIXES = {
    'select': '-select',
    'over':   'Over',
    'out':    'Out'
}

EVENT_TEMPLATE = 'ON_{}_STATE'
ON_VIEW_CHANGED = 'ON_VIEW_CHANGED'
ON_ALIVE_STATE_CHANGED = 'ON_ALIVE_STATE_CHANGED'

###

class __RepairControlStorage(object):

    def __init__(self):
        self.isAlive = True
        self.isWheeledTech = False
        self.crewRoles = []
        self.contused = []
        self.destroyed = []
        self.selected = None
        self.crosshairMode = None
        
        self.lastComplex = None
        self.complexStates = {}
        self.states = {}
        for item in EVENTABLE_ITEMS:
            self.states.update({item: 'normal'})

    def log(self, msg):
        print('[RepairControl]: {}'.format(msg))

    def setAlive(self, isAlive):
        self.isAlive = isAlive
        as_event(ON_ALIVE_STATE_CHANGED)

    def setData(self, vehicle):
        self.isWheeledTech = vehicle.isWheeledTech
        
        for role in vehicle.typeDescriptor.type.crewRoles:
            self.crewRoles.append(role[0])
            #One and more tankman(s) can work for few roles. Don`t forget it!
            #First in role-list - that tankman.
        
        self.setAlive(vehicle.isAlive())

    def eventHandler(self, eventItem):
        if eventItem in EVENTABLE_ITEMS:
            as_event(EVENT_TEMPLATE.format(eventItem.upper()))
        else:
            self.log('"%s" is not an eventable item!' % eventItem)

    def resetSelected(self):
        if self.selected is not None:
            _oldSelected = self.selected
            self.selected = None
            self.eventHandler(_oldSelected[:-4])

    def updateCrosshairMode(self, eMode):
        self.crosshairMode = eMode
        as_event(ON_VIEW_CHANGED)

    def getCrewRoleActive(self, role):
        return self.getTankmanWOIndex(role) in self.crewRoles

    def getComplexType(self):
        return WHEEL if self.isWheeledTech else CHASSIS

    def getCrewState(self, crew):
        return self.states[crew]

    def getDeviceState(self, device):
        return self.states[device]

    def getTankmanWOIndex(self, tankmanWIndex):
        return tankmanWIndex.replace('1', '').replace('2', '')

    def getContusedTankmanWIndex(self, tankmanWOIndex):
        if (tankmanWOIndex in CREW) and self.contused:
            for tankman in self.contused:
                if tankmanWOIndex in tankman:
                    return tankman
        else:
            return tankmanWOIndex

    def getItemStateFormat(self, item):
        deviceState = self.getDeviceState(item)
        return deviceState if (self.selected != item + PREFIXES['over']) else (deviceState + PREFIXES['select'])

###

class RepairControlModule(__RepairControlStorage, object):

    def __init__(self):
        for item in EVENTABLE_ITEMS:
            as_callback(item, self.repairHandler)
            as_callback(item + PREFIXES['over'], self.callbackOnMouseOver)
            as_callback(item + PREFIXES['out'], self.callbackOnMouseOut)
        super(RepairControlModule, self).__init__()

    def reset(self):
        super(RepairControlModule, self).__init__()

    def callbackOnMouseOver(self, data):
        self.selected = data['name']
        self.eventHandler(self.selected[:-4])

    def callbackOnMouseOut(self, data):
        self.selected = None
        self.eventHandler(data['name'][:-3])

    def useEquipment(self, intCD, entityName, sessionProvider):
        res, err = sessionProvider.shared.equipments.changeSetting(intCD, entityName, player())
        if not res and err: 
            sessionProvider.shared.messages.showVehicleError(err.key, err.ctx)
        else:
            if self.contused and (entityName in self.contused):
                self.contused.remove(entityName)

    def repairHandler(self, data):
        sessionProvider = dependency.instance(IBattleSessionProvider)
        equipments = sessionProvider.shared.equipments
        item = data['name']
        if item in DEVICES:
            if (item == FUELTANK) and isVehicleInFire():
                self.useEquipment(REPAIR_ITEMS['extinguisher'], None, sessionProvider)
                return
            elif item == COMPLEX:
                if self.lastComplex is not None:
                    item = self.lastComplex
                elif self.complexStates:
                    if 'destroyed' in self.complexStates.values():
                        for compl in self.complexStates:
                            if compl == 'destroyed':
                                item = compl
                                break
                    elif 'critical' in self.complexStates.values():
                        for compl in self.complexStates:
                            if compl == 'critical':
                                item = compl
                                break
            
            if equipments.hasEquipment(REPAIR_ITEMS['repair_kit']):
                self.useEquipment(REPAIR_ITEMS['repair_kit'], item, sessionProvider)
            elif equipments.hasEquipment(REPAIR_ITEMS['g_repair_kit']):
                self.useEquipment(REPAIR_ITEMS['g_repair_kit'], item, sessionProvider)
        
        elif item in CREW:
            if equipments.hasEquipment(REPAIR_ITEMS['med_kit']):
                self.useEquipment(REPAIR_ITEMS['med_kit'], self.getContusedTankmanWIndex(item), sessionProvider)
            elif equipments.hasEquipment(REPAIR_ITEMS['g_med_kit']):
                self.useEquipment(REPAIR_ITEMS['g_med_kit'], self.getContusedTankmanWIndex(item), sessionProvider)

    def updateDeviceState(self, item, state):
        if item in VEHICLE_DEVICE_IN_COMPLEX_ITEM.keys(): #Tracks or Wheels
            if state == 'normal':
                if item in self.complexStates:
                    del self.complexStates[item]
            else:
                self.complexStates.update({item: state})
            
            if state == 'destroyed':
                self.lastComplex = item
            elif item == self.lastComplex:
                self.lastComplex = None
            
            item = COMPLEX
            complexStatesValues = self.complexStates.values()
            self.states[item] = 'destroyed' if ('destroyed' in complexStatesValues) else 'critical' if ('critical' in complexStatesValues) else 'normal'
        
        elif item in VEHICLE_GUI_ITEMS:
             self.states[item] = state
        
        elif self.getTankmanWOIndex(item) in CREW:
            if state == 'destroyed':
                self.contused.append(item) 
            elif (state == 'normal') and (item in self.contused):
                self.contused.remove(item)
            item = self.getTankmanWOIndex(item)
            self.states[item] = state
        
        self.eventHandler(item)

RepairControl = RepairControlModule()

###

@registerEvent(Vehicle, 'onEnterWorld')
def onEnterWorld(self, prereqs):
    if self.isPlayerVehicle:
        RepairControl.setData(self)

@registerEvent(PlayerAvatar, 'handleKey')
def handleKey(self, isDown, key, mods):
    if key == Keys.KEY_LCONTROL:
        RepairControl.resetSelected()

@registerEvent(Vehicle, '_Vehicle__onVehicleDeath')
def onVehicleDeath(self, isDeadStarted = False):
    if self.isPlayerVehicle:
        RepairControl.setAlive(False)

@registerEvent(DamagePanel, '_updateDeviceState')
def _updateDeviceState(self, value):
    RepairControl.updateDeviceState(value[0], value[2])

@registerEvent(DamagePanel, '_updateCrewDeactivated')
def _updateCrewDeactivated(self, _):
    RepairControl.reset()

@registerEvent(DamagePanel, '_updateDestroyed')
def _updateDestroyed(self, _ = None):
    RepairControl.reset()

@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def onControlModeChanged(self, eMode, **args):
    RepairControl.updateCrosshairMode(eMode)

@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def destroyGUI(self):
    RepairControl.reset()

###

@xvm.export('repairControl.getYWOffset', deterministic=False)
def getYWOffset(defVal, yOffset):
    return (defVal - yOffset) if (RepairControl.crosshairMode in (CTRL_MODE_NAME.SNIPER, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.ARTY)) else defVal

@xvm.export('repairControl.isAlive', deterministic=False)
def isAlive():
    return 'alive' if RepairControl.isAlive else ''

@xvm.export('repairControl.complexType', deterministic=False)
def complexType():
    return RepairControl.getComplexType()

@xvm.export('repairControl.engineState', deterministic=False)
def engineState():
    return RepairControl.getItemStateFormat(ENGINE)

@xvm.export('repairControl.ammoBayState', deterministic=False)
def ammoBayState():
    return RepairControl.getItemStateFormat(AMMOBAY)

@xvm.export('repairControl.gunState', deterministic=False)
def gunState():
    return RepairControl.getItemStateFormat(GUN)

@xvm.export('repairControl.turretState', deterministic=False)
def turretState():
    return RepairControl.getItemStateFormat(TURRET)

@xvm.export('repairControl.complexState', deterministic=False)
def complexState():
    return RepairControl.getItemStateFormat(COMPLEX)

@xvm.export('repairControl.surveyingState', deterministic=False)
def surveyingState():
    return RepairControl.getItemStateFormat(SURVEYING)

@xvm.export('repairControl.radioState', deterministic=False)
def radioState():
    return RepairControl.getItemStateFormat(RADIO)

@xvm.export('repairControl.fuelTankState', deterministic=False)
def fuelTankState():
    return RepairControl.getItemStateFormat(FUELTANK)

@xvm.export('repairControl.commanderState', deterministic=False)
def commanderState():
    return RepairControl.getItemStateFormat(COMMANDER)

@xvm.export('repairControl.radiomanState', deterministic=False)
def radiomanState():
    return RepairControl.getItemStateFormat(RADIOMAN)

@xvm.export('repairControl.driverState', deterministic=False)
def driverState():
    return RepairControl.getItemStateFormat(DRIVER)

@xvm.export('repairControl.gunnerState', deterministic=False)
def gunnerState():
    return RepairControl.getItemStateFormat(GUNNER)

@xvm.export('repairControl.loaderState', deterministic=False)
def loaderState():
    return RepairControl.getItemStateFormat(LOADER)

@xvm.export('repairControl.isRoleActive', deterministic=False)
def isRoleActive(role):
    return RepairControl.getCrewRoleActive(role)
