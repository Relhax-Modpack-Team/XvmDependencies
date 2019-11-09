from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import SpeedometerWheeledTech
from gui.battle_control.battle_constants import CROSSHAIR_VIEW_ID

from xfw import *
from xvm_main.python.logger import *
import xvm_main.python.config as config


@overrideMethod(SpeedometerWheeledTech, 'start')
def SpeedometerWheeledTech_start(base, self):
    value = config.get('sight/showSpeedometer', 'wheels').lower()
    if config.get('sight/enabled', True) and value == 'all':
        base(self)
        vStateCtrl = self.sessionProvider.shared.vehicleState
        if vStateCtrl is not None:
            vehicle = vStateCtrl.getControllingVehicle()
            if vehicle is not None and not vehicle.isWheeledTech:
                self._SpeedometerWheeledTech__onVehicleControlling(vehicle)
    else:
        base(self)


@overrideMethod(SpeedometerWheeledTech, '_SpeedometerWheeledTech__onVehicleControlling')
def SpeedometerWheeledTech__onVehicleControlling(base, self, vehicle):
    if not config.get('sight/enabled', True):
        return base(self, vehicle)
    value = config.get('sight/showSpeedometer', 'wheels').lower()
    if value == 'all' and not vehicle.isWheeledTech:
        vStateCtrl = self.sessionProvider.shared.vehicleState
        self._SpeedometerWheeledTech__addSpedometer(vehicle)
        self._SpeedometerWheeledTech__updateCurStateSpeedMode(vStateCtrl)
    elif value == 'none':
        self.parentObj.as_removeSpeedometerS()
    else:
        base(self, vehicle)


@overrideMethod(SpeedometerWheeledTech, '_SpeedometerWheeledTech__onCrosshairViewChanged')
def SpeedometerWheeledTech__onCrosshairViewChanged(base, self, viewID):
    if not config.get('sight/enabled', True):
        return base(self, viewID)
    value = config.get('sight/showSpeedometer', 'wheels').lower()
    if value == 'all':
        vStateCtrl = self.sessionProvider.shared.vehicleState
        vehicle = vStateCtrl.getControllingVehicle()
        if vehicle is not None and viewID == CROSSHAIR_VIEW_ID.ARCADE:
            self._SpeedometerWheeledTech__onVehicleControlling(vehicle)
            self._SpeedometerWheeledTech__updateCurStateSpeedMode(vStateCtrl)
    elif value == 'none':
        return
    else:
        base(self, viewID)
