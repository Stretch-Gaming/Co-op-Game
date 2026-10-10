"""Primary-owned test-only spawn helpers; no production package changes."""
import sys,importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
bp=ue.load_asset('/Game/Puzzles/Test/HC_Gauntlet/BP_FixtureLatchBridge')
for name,path in [('SpawnPrimaryCoordinator','/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator.BP_HCGauntletCoordinator_C'),('SpawnPrimaryBridge','/Game/Puzzles/Gauntlet/BP_HCGauntletGateBridge.BP_HCGauntletGateBridge_C')]:
 fn(bp,name,[],[('Spawned',ue.Actor.static_class())])
compile_bp(bp)
for name,path in [('SpawnPrimaryCoordinator','/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator.BP_HCGauntletCoordinator_C'),('SpawnPrimaryBridge','/Game/Puzzles/Gauntlet/BP_HCGauntletGateBridge.BP_HCGauntletGateBridge_C')]:
 write(bp,name,'(bind spawned (Game|SpawnActorfromClass :Class "'+path+'" :SpawnTransform (Transformation|GetActorTransform))) (return spawned)')
save(bp)
snapshot([bp],'primary-fixture-spawns.json')
