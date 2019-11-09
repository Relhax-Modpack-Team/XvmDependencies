import BigWorld
import BattleReplay
from xvm_main.python.logger import *


@xvm.export('xvm.lag', deterministic=False)
def xvm_lag():
    replayCtrl = BattleReplay.g_replayCtrl
    if replayCtrl.isPlaying and replayCtrl.fps > 0:
        isLaggingNow = 'lag' if replayCtrl.isLaggingNow else None
    else:
        isLaggingNow = 'lag' if BigWorld.statLagDetected() else None
    # log('lag = %s' % isLaggingNow)
    return isLaggingNow


@xvm.export('xvm.ping', deterministic=False)
def xvm_ping():
    replayCtrl = BattleReplay.g_replayCtrl
    if replayCtrl.isPlaying and replayCtrl.fps > 0:
        ping = replayCtrl.ping
    else:
        ping = BigWorld.statPing()
    return int(ping)


@xvm.export('xvm.fps', deterministic=False)
def xvm_fps():
    return int(BigWorld.getFPS()[1])


@xvm.export('xvm.fps_replay', deterministic=False)
def xvm_fps_replay():
    replayCtrl = BattleReplay.g_replayCtrl
    return int(replayCtrl.fps) if replayCtrl.isPlaying and replayCtrl.fps > 0 else None