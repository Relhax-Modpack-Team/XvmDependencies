import gui.Scaleform.daapi.view.battle.shared.crosshair.plugins as plug
from gui.Scaleform.daapi.view.meta.CrosshairPanelContainerMeta import CrosshairPanelContainerMeta
from gui.Scaleform.genConsts.CROSSHAIR_CONSTANTS import CROSSHAIR_CONSTANTS
from gui.battle_control.battle_constants import CROSSHAIR_VIEW_ID

import xvm_battle.python.battle as battle
import xvm_main.python.config as config
from xfw.events import registerEvent, overrideMethod
from xvm_main.python.logger import *


@overrideMethod(CrosshairPanelContainerMeta, 'as_setDistanceS')
def CrosshairPanelContainerMeta_as_setDistanceS(base, self, dist):
    if not (config.get('sight/enabled', True) and config.get('sight/removeDistance', False)):
        return base(self, dist)


@overrideMethod(CrosshairPanelContainerMeta, 'as_setNetVisibleS')
def CrosshairPanelContainerMeta_as_setNetVisibleS(base, self, mask):
    if config.get('sight/enabled', True):
        if config.get('sight/removeIndicator', False):
            mask &= 2
        if config.get('sight/removeQuantityShells', False):
            mask &= 1
    return base(self, mask)


@registerEvent(plug.SiegeModePlugin, '_SiegeModePlugin__updateView')
def SiegeModePlugin__updateView(self):
    if config.get('sight/enabled', True):
        vStateCtrl = self.sessionProvider.shared.vehicleState
        vehicle = vStateCtrl.getControllingVehicle()
        if vehicle is not None:
            vTypeDescr = vehicle.typeDescriptor
            if vTypeDescr.isWheeledVehicle or vTypeDescr.hasAutoSiegeMode:
                self._parentObj.as_setNetVisibleS(CROSSHAIR_CONSTANTS.VISIBLE_NET)
    return


@overrideMethod(CrosshairPanelContainerMeta, 'as_setViewS')
def CrosshairPanelContainerMeta_as_setViewS(base, self, viewId, settingId):
    isHide = viewId == CROSSHAIR_VIEW_ID.POSTMORTEM and config.get('sight/hideSightAfterDeath', False) and config.get('sight/enabled', True)
    return base(self, viewId, settingId) if not isHide else base(self, -1, -1)


@overrideMethod(plug, '_makeSettingsVO')
def plugins_makeSettingsVO(base, settingsCore, *keys):
    data = base(settingsCore, *keys)
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        for mode in data:
            if config.get('sight/removeCentralMarker', False) and ('centerAlphaValue' in data[mode]):
                data[mode]['centerAlphaValue'] = 0
            if config.get('sight/removeIndicator', False) and config.get('sight/removeQuantityShells', False) and ('netAlphaValue' in data[mode]):
                data[mode]['netAlphaValue'] = 0
            if config.get('sight/removeLoad', False) and ('reloaderAlphaValue' in data[mode]):
                data[mode]['reloaderAlphaValue'] = 0
            if config.get('sight/removeCondition', False) and ('conditionAlphaValue' in data[mode]):
                data[mode]['conditionAlphaValue'] = 0
            if config.get('sight/removeContainers', False) and ('cassetteAlphaValue' in data[mode]):
                data[mode]['cassetteAlphaValue'] = 0
            if config.get('sight/removeLoadingTimer', False) and ('reloaderTimerAlphaValue' in data[mode]):
                data[mode]['reloaderTimerAlphaValue'] = 0
            if config.get('sight/removeZoomIndicator', False) and ('zoomIndicatorAlphaValue' in data[mode]):
                data[mode]['zoomIndicatorAlphaValue'] = 0
    return data
