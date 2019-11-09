from xfw import *
import messenger.gui.Scaleform.view.battle.messenger_view as messenger_view

@overrideMethod(messenger_view, '_makeSettingsVO')
def _makeSettingsVO(base,arenaVisitor):
    makeSettingsVO = base(arenaVisitor)
    makeSettingsVO['maxLinesCount'] = 8
    return makeSettingsVO