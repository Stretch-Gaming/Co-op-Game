import sys,importlib,json,unreal as ue
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
path='/Game/Puzzles/EnvironmentConnection/BP_EnvironmentDoor'
bp=ue.load_asset(path)
if not bp:
 bp=ue.EditorAssetLibrary.duplicate_asset('/Game/Puzzles/Gauntlet/BP_HCGauntletObjective',path);assert bp
 for graph in list(BP.list_graphs(bp)):
  name=graph.get_name()
  if name not in ('UserConstructionScript','EventGraph','CanInteract','GetInteractInfo'):BP.remove_function_graph(bp,name)
  else:
   for node in list(BP.find_nodes(graph)):
    if name in ('EventGraph','UserConstructionScript') or not isinstance(node,(ue.K2Node_FunctionEntry,ue.K2Node_FunctionResult)):BP.delete_node(node)
 for name in list(BP.list_variables(bp)):BP.remove_variable(bp,name)
compile_bp(bp)
var(bp,'Open','bool',False,replicated=True);var(bp,'ClosedLocation','Vector',ue.Vector())
for name in ('InitializeDoor','MoveDoor'):fn(bp,name,inputs=[('DeltaSeconds','float')] if name=='MoveDoor' else [])
fn(bp,'OpenFromPlayer',inputs=[('Instigator',ue.Actor.static_class())])
write(bp,'CanInteract','''(bind pawn (Utilities|Casting|CastToPawn :Object Instigator) (:then (return (and (not (Variables|Default|GetOpen)) (Pawn|IsPlayerControlled :self pawn)))) (:CastFailed (return false)))''','Instigator')
write(bp,'GetInteractInfo','(return "Open the door" 0.0 (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator0"))','Instigator')
write(bp,'OpenFromPlayer','''(if (Networking|HasAuthority) (bind allowed (CallFunction|CanInteract :Instigator Instigator)) (if allowed (Variables|Default|SetOpen true)))''','Instigator')
write(bp,'InitializeDoor','(if (Networking|HasAuthority) (Variables|Default|SetClosedLocation (Transformation|GetActorLocation)))')
write(bp,'MoveDoor','''(if (and (Networking|HasAuthority) (Variables|Default|GetOpen)) (bind target (+ (Variables|Default|GetClosedLocation) (Math|Vector|MakeVector :Z 450.0))) (bind next (Math|Interpolation|VInterptoConstant :Current (Transformation|GetActorLocation) :Target target :DeltaTime DeltaSeconds :InterpSpeed 600.0)) (Transformation|SetActorLocation :NewLocation next :bSweep false :bTeleport true))''','DeltaSeconds')
event(bp,'Interact','OpenFromPlayer',['Instigator']);event(bp,'ReceiveBeginPlay','InitializeDoor');event(bp,'ReceiveTick','MoveDoor',['DeltaSeconds'])
cdo=BP.get_default_object(bp);cdo.set_editor_properties({'replicates':True,'replicate_movement':True,'always_relevant':True})
mesh=cdo.static_mesh_component;mesh.set_static_mesh(ue.load_asset('/Game/Puzzles/Art/HCA2_Props/SM_ChamberGate_Leaf'));mesh.set_mobility(ue.ComponentMobility.MOVABLE);mesh.set_collision_profile_name('BlockAll');mesh.set_simulate_physics(False);mesh.set_enable_gravity(False)
# The preview door is independent of rounds/plates. It uses the existing interaction interface only.
save(bp)
RESULT={'door':path,'compiled':True,'puzzle_dependencies':False,'interaction':'E opens door once; server moves it; replicated actor movement'}
(OUTPUT/'door-build.json').write_text(json.dumps(RESULT,indent=2))
