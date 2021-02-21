import BigWorld
import Keys
import game
from Vehicle import Vehicle
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID as _FET
from gui.battle_control.controllers.feedback_adaptor import BattleFeedbackAdaptor
# from gui.app_loader import g_appLoader
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader

import xvm_main.python.config as config
from xfw.events import registerEvent
from xvm_main.python.logger import *

settingsPM = {'enable': True, 'key': Keys.KEY_N, 'marker': False, 'proxy': None, 'arenaDP': None}


def initPM():
    global settingsPM
    settingsPM = {'enable': False, 'key': Keys.KEY_N, 'marker': False, 'proxy': None, 'arenaDP': None}
    settingsPM['enable'] = config.get('markers/playerMarkers/onStart', False)
    settingsPM['key'] = config.get('markers/playerMarkers/keyCode', Keys.KEY_N)


@registerEvent(BattleFeedbackAdaptor, 'startVehicleVisual')
def BattleFeedbackAdaptor_startVehicleVisual(self, vProxy, isImmediate=False):
    if vProxy.isPlayerVehicle:
        initPM()
        settingsPM['proxy'] = vProxy
        settingsPM['arenaDP'] = self._BattleFeedbackAdaptor__arenaDP
        vInfo = settingsPM['arenaDP'].getVehicleInfo(vProxy.id)
        if settingsPM['enable']:
            self.onVehicleMarkerAdded(vProxy, vInfo, settingsPM['arenaDP'].getPlayerGuiProps(vProxy.id, vInfo.team))
            settingsPM['marker'] = True


@registerEvent(BattleFeedbackAdaptor, 'stopVehicleVisual')
def BattleFeedbackAdaptor_stopVehicleVisual(self, vehicleID, isPlayerVehicle):
    if isPlayerVehicle and settingsPM['marker']:
        self.onVehicleMarkerRemoved(vehicleID)
        settingsPM['marker'] = False
    return


@registerEvent(Vehicle, '_Vehicle__onVehicleDeath')
def Vehicle__onVehicleDeath(self, isDeadStarted=False):
    if self.isPlayerVehicle and settingsPM['marker']:
        self.guiSessionProvider.shared.feedback.onVehicleFeedbackReceived(_FET.VEHICLE_DEAD, self.id, isDeadStarted)


@registerEvent(Vehicle, 'onHealthChanged')
def Vehicle_onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID):
    if self.isPlayerVehicle and settingsPM['marker']:
        self.guiSessionProvider.shared.feedback.setVehicleNewHealth(self.id, newHealth, attackerID, attackReasonID)


@registerEvent(game, 'handleKeyEvent')
def game_handleKeyEvent(event):
    isDown, key, mods, isRepeat = game.convertKeyEvent(event)
    if mods == 0 and isDown and settingsPM['proxy'] is not None:
        app = dependency.instance(IAppLoader)
        player = BigWorld.player()
        if key == settingsPM['key'] and app.getDefBattleApp() and player.inputHandler.isGuiVisible:
            if settingsPM['marker']:
                player.guiSessionProvider.shared.feedback.onVehicleMarkerRemoved(settingsPM['proxy'].id)
                settingsPM['marker'] = False
            else:
                vInfo = settingsPM['arenaDP'].getVehicleInfo(settingsPM['proxy'].id)
                player.guiSessionProvider.shared.feedback.onVehicleMarkerAdded(settingsPM['proxy'], vInfo, settingsPM['arenaDP'].getPlayerGuiProps(settingsPM['proxy'].id, vInfo.team))
                settingsPM['marker'] = True
