import BigWorld
from xfw.events import registerEvent
from xfw_actionscript.python import *
import xfw
from xvm_main.python.stats import _Stat
from Avatar import PlayerAvatar
from gui.battle_control import avatar_getter
from constants import ARENA_GUI_TYPE


class _cfg(object):

    def __init__(self):
        self.enabled = True
        self.ArenaReady = False
        self.players = {}
        self.players_xvm = {}

    def reset(self):
        self.__init__()

cfg = _cfg()


def checkBattleType():
    arena = getattr(BigWorld.player(), 'arena', None)
    if arena is not None:
        cfg.ArenaReady = True
        if arena.guiType != ARENA_GUI_TYPE.RANDOM:
            cfg.enabled = False

@xfw.registerEvent(_Stat, '_addContactData')
def _Stat__addContactData(self, stat):
    name = stat.get('xvm_contact_data').get('nick')
    if name is not None:
        if name not in cfg.players_xvm:
            cfg.players_xvm[name] = {'org_name': stat.get['name']}

def refreshPlayers():
    if not cfg.enabled:
        return
    arena = avatar_getter.getArena()
    if arena is not None:
        for (vehicleID, vData) in arena.vehicles.iteritems():
            if vData['name'] not in cfg.players:
                cfg.players[vData['name']] = {'accountDBID':vData['accountDBID']}

@xvm.export('IsAnonym')
def IsAnonym(name):
    result = 0
    if not cfg.enabled:
        return result
    if name in cfg.players_xvm:
        name = cfg.players_xvm[name].get('org_name')
    if name not in cfg.players:
        refreshPlayers()
    if name in cfg.players:
        result = 100 if cfg.players[name]['accountDBID'] == 0 else 0
    return result


@registerEvent(PlayerAvatar, '_PlayerAvatar__startGUI')
def __startGUI(self):
    cfg.reset()
    if not cfg.ArenaReady:
        checkBattleType()
    refreshPlayers()

@registerEvent(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def PlayerAvatar__destroyGUI(self):
    cfg.reset()
