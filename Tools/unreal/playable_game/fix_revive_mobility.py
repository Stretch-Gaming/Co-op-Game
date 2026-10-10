import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
proxy=ue.load_asset('/Game/Puzzles/Recovery/BP_HCReviveTarget');mesh,h=component(proxy,'StaticMeshComponent',ue.StaticMeshComponent);mesh.set_mobility(ue.ComponentMobility.MOVABLE);save(proxy)
RESULT={'revive_proxy_can_follow_player':True}
