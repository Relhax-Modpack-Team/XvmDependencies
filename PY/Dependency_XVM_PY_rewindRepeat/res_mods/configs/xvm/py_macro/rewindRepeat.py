import BigWorld
import Keys
from BattleReplay import BattleReplay, REPLAY_TIME_MARK_REPLAY_FINISHED, REPLAY_TIME_MARK_CURRENT_TIME, FAST_FORWARD_STEP
from helpers import isPlayerAvatar

from xfw import *
from xvm_main.python.logger import *


accelerate = {Keys.KEY_NONE: 1,
              Keys.MODIFIER_SHIFT: 3,
              Keys.MODIFIER_CTRL: 6,
              Keys.MODIFIER_ALT: 15}


@overrideMethod(BattleReplay, 'handleKeyEvent')
def BattleReplay_handleKeyEvent(base, self, isDown, key, mods, isRepeat, event):
    if key not in [Keys.KEY_LEFTARROW, Keys.KEY_RIGHTARROW]:
        return base(self, isDown, key, mods, isRepeat, event)
    if not self.isPlaying:
        return False
    if self.isBattleSimulation:
        return False
    if self.isTimeWarpInProgress:
        return True
    if not self.isClientReady:
        return False
    player = BigWorld.player()
    if not isPlayerAvatar():
        return False
    if not player.isForcedGuiControlMode():
        self._BattleReplay__isMenuShowed = False
    if self._BattleReplay__isMenuShowed:
        return False
    currReplayTime = self._BattleReplay__replayCtrl.getTimeMark(REPLAY_TIME_MARK_CURRENT_TIME)
    finishReplayTime = self._BattleReplay__replayCtrl.getTimeMark(REPLAY_TIME_MARK_REPLAY_FINISHED)
    if currReplayTime > finishReplayTime:
        currReplayTime = finishReplayTime
    fastForwardStep = FAST_FORWARD_STEP * accelerate.get(mods, 1)
    if key == Keys.KEY_RIGHTARROW and isDown and not self._BattleReplay__isFinished:
        self._BattleReplay__timeWarp(currReplayTime + fastForwardStep)
        return True
    if key == Keys.KEY_LEFTARROW:
        self._BattleReplay__timeWarp(currReplayTime - fastForwardStep)
        return True
    return False