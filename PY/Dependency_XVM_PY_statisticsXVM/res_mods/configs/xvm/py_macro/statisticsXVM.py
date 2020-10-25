# Authors:
# night_dragon_on <https://kr.cm/f/p/14897/>

#####################################################################
# imports

import BigWorld
from debug_utils import LOG_ERROR
from helpers import getClientLanguage
from gui.Scaleform.daapi.view.lobby.messengerBar.VehicleCompareCartButton import VehicleCompareCartButton
from gui.Scaleform.daapi.view.meta.MessengerBarMeta import MessengerBarMeta

import xvm_main.python.utils as utils
from xfw.events import registerEvent
from xfw_actionscript.python import as_event, as_callback

#####################################################################
# constants

buttonsState = None
countVehicles = None

if getClientLanguage() == 'ru':
    url = 'https://stats.modxvm.com/ru/stat/players/'
else:
    url = 'https://stats.modxvm.com/en/stat/players/'

#####################################################################
# handlers

def _stats_down(data):
    if data['buttonIdx'] == 0:
        accountDBID = utils.getAccountDBID()
        try:
            BigWorld.wg_openWebBrowser(url + str(accountDBID))
        except Exception:
            LOG_ERROR('statisticsXVM: there is error while opening web browser')
    return

as_callback('stats_mouseDown', _stats_down)

@registerEvent(VehicleCompareCartButton, '_populate')
def _populate(self):
    global buttonsState, countVehicles
    countVehicles = self.comparisonBasket.getVehiclesCount()
    if countVehicles > 0:
        buttonsState = True
        as_event('ON_VC_BST')

@registerEvent(VehicleCompareCartButton, '_VehicleCompareCartButton__onCountChanged')
def onCountChanged(self, _, __):
    global countVehicles
    countVehicles = self.comparisonBasket.getVehiclesCount()

@registerEvent(MessengerBarMeta, 'as_setVehicleCompareCartButtonVisibleS')
def as_setVehicleCompareCartButtonVisibleS(self, value):
    global buttonsState    
    if (value == True) and (countVehicles > 0):
        buttonsState = True
    elif (value == False) and (countVehicles == 0):
        buttonsState = None
    else:
        return
    as_event('ON_VC_BST')

@xvm.export('vc.buttonsState', deterministic=False)
def vc_buttonsState():
    return buttonsState