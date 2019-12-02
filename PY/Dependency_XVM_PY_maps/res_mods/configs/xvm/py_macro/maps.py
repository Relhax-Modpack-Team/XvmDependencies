import BigWorld
from items.vehicles import CAMOUFLAGE_KIND_INDICES

from xfw import *
from xvm_main.python.logger import *


@xvm.export('map.kind', deterministic=True)
def maps_mapKind():
    return CAMOUFLAGE_KIND_INDICES.get(BigWorld.player().guiSessionProvider.arenaVisitor.type.getVehicleCamouflageKind(), None)


@xvm.export('map.nameFile', deterministic=True)
def maps_nameFileMap():
    return BigWorld.player().guiSessionProvider.arenaVisitor.type.getGeometryName()


@xvm.export('map.localeName', deterministic=True)
def maps_localeNameMap():
    return BigWorld.player().guiSessionProvider.arenaVisitor.type.getName()


