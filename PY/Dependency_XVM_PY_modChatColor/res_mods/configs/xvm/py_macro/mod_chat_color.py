import re
import string

from debug_utils import _doLog

from messenger.gui.Scaleform.channels.bw_chat2.battle_controllers import TeamChannelController
from messenger.formatters.chat_message import TeamMessageBuilder
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from messenger_common_chat2 import MESSENGER_ACTION_IDS

from xvm_main.python.stats import _stat
import xvm_main.python.utils as xvm_utils
import xvm_main.python.config as config

def dump(obj):
    values = []
    for name in dir(obj):
        attr = getattr(obj, name)
        if callable(attr):
            if name.startswith('get') or name.startswith('is'):
                values.append('%s=%s' % (name, attr()))

    return '[%s]' % (', '.join(values))

def LOG_ERROR(msg, *kargs, **kwargs):
    if config.get('chat/logLevel', 0) >= 0:
        _doLog('ERROR', msg, kargs, kwargs)

def LOG_WARN(msg, *kargs, **kwargs):
    if config.get('chat/logLevel', 0) >= 1:
        _doLog('WARNING', msg, kargs, kwargs)

def LOG_INFO(msg, *kargs, **kwargs):
    if config.get('chat/logLevel', 0) >= 2:
        _doLog('INFO', msg, kargs, kwargs)

def LOG_DEBUG(msg, *kargs, **kwargs):
    if config.get('chat/logLevel', 0) >= 3:
        _doLog('DEBUG', msg, kargs, kwargs)

LOG_DEBUG('LOADING')

# http://stackoverflow.com/a/19800610/5099839
class StatsFormatter(string.Formatter):
    def __init__(self, default=0):
        self.default = default

    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            v = kwargs.get(key, self.default)
            return 0 if v is None else v
        else:
            Formatter.get_value(key, args, kwargs)

class ChatColor(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)
    # PlayerName_re matches "Name (Vehicle)", "Name[CLAN] (Vehicle)", and "Name[CLAN] (Vehicle (x))"
    PlayerName_re = re.compile(r'([^\s><\[]+)(\[[^\]]*\])?( \((?:[^\(\)]|\([^\)]*\))+\))')

    def __init__(self):
        LOG_DEBUG('ChatColor.__init__()')

        ChatColor._TeamChannelController_formatCommand = TeamChannelController._formatCommand
        TeamChannelController._formatCommand = ChatColor.TeamChannelController_formatCommand

        ChatColor._TeamChannelController_formatMessage = TeamChannelController._formatMessage
        TeamChannelController._formatMessage = ChatColor.TeamChannelController_formatMessage

        # Hooking TeamMessageBuilder.setColors() is not enough to set the color of enemy target
        #ChatColor._TeamMessageBuilder_setColors = TeamMessageBuilder.setColors
        #TeamMessageBuilder.setColors = ChatColor.TeamMessageBuilder_setColors

    @staticmethod
    def getVehIDByPlayerName(playerName):
        # FIXME: build a map during battle startup and stop iterating every time
        for vo in ChatColor.sessionProvider.getArenaDP().getVehiclesInfoIterator():
            if vo.player.name == playerName:
                return vo.vehicleID
        return None

    @staticmethod
    def getPlayerStats(vehicleID):
        # Retrieve player rating and associated color
        # FIXME: is there any API to retrieve the cached stats from Python!?
        if vehicleID in _stat.players:
            pl = _stat.players.get(vehicleID)
            cacheKey = "%d=%d" % (pl.accountDBID, pl.vehCD)
            if cacheKey in _stat.cacheBattle:
                return ChatColor.fixStats(_stat.cacheBattle[cacheKey])

        return None

    @staticmethod
    def fixStats(stats):
        if stats is None:
            return None

        stats = stats.copy()
        rating = config.networkServicesSettings.rating

        if not stats.has_key('xte') and stats.has_key('v') and stats['v'].has_key('xte'):
            stats['xte'] = stats['v']['xte']

        stats['r'] = stats.get(rating, 0)
        stats['xr'] = stats['r'] if rating.startswith('x') else stats.get('x' + rating, 0)
        stats['cr'] = ChatColor.getRatingColor(stats)

        # Stats for new players are incomplete, so use default values (StatsFormatter does most of the job)
        stats['flag'] = stats.get('flag', 'default')

        return stats

    @staticmethod
    def getRatingColor(stats):
        if stats is None:
            return None

        rating = config.networkServicesSettings.rating
        v = stats.get(rating, 0)
        if config.get('chat/customColors', False):
            # Use custom colors from chat.xc
            v = stats.get('x' + rating, v) # normalized rating only
            colors = config.get('chat/colors', None)
            if colors is None:
                color = ''
            else:
                color = next((int(x['color'], 0) for x in colors if v <= float(x['value'])), 0xFFFFFF)
                color = "#{0:06x}".format(color)
        else:
            # Use colors from colors.xc
            color = xvm_utils.getDynamicColorValue('x' if rating.startswith('x') else rating, v if v is not None else 0)

        LOG_DEBUG('%s/%s => %s' % (rating, v, color))
        return color

    @staticmethod
    def buildExtra(stats, name):
        if stats is None:
            return ''

        extra = config.get('chat/%s' % name, '')
        return xvm_utils.fixImgTag(StatsFormatter().format(extra, **stats))

    @staticmethod
    def colorize(msg, cmd=None):
        if cmd is not None:
            # TODO: permit to add prefix/suffix to command message, and change color of message
            pass

        res = u''
        pos = 0
        is_author = True
        for m in ChatColor.PlayerName_re.finditer(msg):
            res += msg[pos:m.start()]
            pos = m.end()

            name = m.group(1)
            clan = m.group(2)
            vname = m.group(3)

            repl = m.group(0)
            vid = ChatColor.getVehIDByPlayerName(name)
            if vid is None:
                LOG_WARN('Cannot find VID for player with name "%s"' % name)
            else:
                stats = ChatColor.getPlayerStats(vid)
                if stats is None:
                    LOG_ERROR('Cannot find stats for player with name "%s"' % name)
                else:
                    color = stats['cr']
                    prefix = ChatColor.buildExtra(stats, 'authorPrefix' if is_author else 'prefix')
                    suffix = ChatColor.buildExtra(stats, 'authorSuffix' if is_author else 'suffix')

                    colorize = config.get('chat/%s' % ('colorizeAuthor' if is_author else 'colorizeTarget'), True)
                    if colorize:
                        repl = "%s<font color='%s'>%s%s%s</font>%s" % (prefix, color, name, clan if clan is not None else '', vname, suffix)
                    else:
                        repl = "%s%s%s%s%s" % (prefix, name, clan if clan is not None else '', vname, suffix)

            res += repl
            is_author = False

        res += msg[pos:]
        LOG_DEBUG("'%s' => '%s'" % (msg, res))

        return res

    @staticmethod
    def TeamChannelController_formatCommand(self, command):
        fmt = ChatColor._TeamChannelController_formatCommand(self, command)
        # LOG_DEBUG('TeamChannelController_formatCommand(%s) using %s => %s' % (command, self._mBuilder, fmt))
        cmd = MESSENGER_ACTION_IDS.battleChatCommandFromActionID(command.getID())
        if cmd is not None:
            cmd = dict(cmd_name=cmd.msgText, cmd_id=command.getID())
            # LOG_DEBUG(cmd)
        return (fmt[0], ChatColor.colorize(fmt[1], cmd))

    @staticmethod
    def TeamChannelController_formatMessage(self, message, doFormatting=True):
        fmt = ChatColor._TeamChannelController_formatMessage(self, message, doFormatting)
        # LOG_DEBUG('TeamChannelController_formatMessage(%s) using %s => %s' % (message, self._mBuilder, fmt))
        return (fmt[0], ChatColor.colorize(fmt[1]))

    @staticmethod
    def TeamMessageBuilder_setColors(self, dbID):
        ChatColor._TeamMessageBuilder_setColors(self, dbID)

        vehicleID = ChatColor.sessionProvider.getArenaDP().getVehIDByAccDBID(dbID)
        color = ChatColor.getPlayerRatingColor(vehicleID)
        if color is not None:
            self._ctx['playerColor'] = color[1:]    # remove '#' prefix

        return self

ChatColor()

LOG_DEBUG('LOADED')
