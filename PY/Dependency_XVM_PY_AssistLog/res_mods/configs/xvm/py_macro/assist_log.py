from xvm_main.python.logger import *
from xvm import assistLog


@xvm.export('xvm.assistLog', deterministic=False)
def xvm_assistLog():
    return assistLog.getLog()


@xvm.export('xvm.assistLog_Background', deterministic=False)
def xvm_assistLog_Background():
    return assistLog.getBackgroundLog()


@xvm.export('xvm.assistLog_x', deterministic=False)
def xvm_assistLog_x():
    return assistLog.getLogX()


@xvm.export('xvm.assistLog_y', deterministic=False)
def xvm_assistLog_y():
    return assistLog.getLogY()
