import sys
import pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import authoring
import importlib
importlib.reload(authoring)
from authoring import *
guard()
A=unreal.Actor.static_class()
C=unreal.ActorComponent.static_class()
carry=unreal.load_asset('/Game/Puzzles/BP_Carryable')
if carry: assert isinstance(BP.get_default_object(carry),unreal.StaticMeshActor), 'Preserve an unexpected existing asset.'
if not carry:
    guard()
    carry=unreal.EditorAssetLibrary.duplicate_asset('/Game/Puzzles/Test/BP_TestInteractable','/Game/Puzzles/BP_Carryable')
ac=create('/Game/Puzzles/Carrying/AC_Carrying',C)

for name,kind,notify in [('Carrier',A,True),('CarryState','int',True),('Heavy','bool',False),('InitialTransform','Transform',False),('CarrierComponent',C,False)]: var(carry,name,kind,notify)
for name,kind,notify in [('CarriedItem',A,True),('CarrySpeed','float',True),('SavedSpeed','float',False),('SpeedActive','bool',False)]: var(ac,name,kind,notify)
carry_fns={
 'ApplyCarryState':([],[]), 'BeginCarryable':([],[]), 'Claim':([('NewCarrier',A),('NewComponent',C)],[('Success','bool')]),
 'Drop':([],[]), 'ReleaseCarried':([],[('Item',A)]), 'ClearCarrier':([],[]),
 'ResetItem':([],[]), 'GetHeavy':([],[('IsHeavy','bool')]), 'CanClaim':([('Instigator',A)],[('Allowed','bool')]),
 'GetCarryState':([],[('State','int'),('Who',A)])}
ac_fns={
 'TryPickup':([('Item',A)],[('Success','bool')]), 'DropCarried':([],[]), 'GetCarried':([],[('Item',A)]),
 'ReleaseCarried':([],[('Item',A)]), 'ApplyCarrySpeed':([],[]), 'ClearCarried':([],[]),
 'BeginCarrying':([],[]), 'EndCarrying':([],[]), 'CanPickup':([('Item',A)],[('Allowed','bool')])}
for bp, funcs in [(carry,carry_fns),(ac,ac_fns)]:
    for name,(ins,outs) in funcs.items(): fn(bp,name,ins,outs)
    compile_bp(bp)
mesh=BP.get_default_object(carry).static_mesh_component
owned(carry)
mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
mesh.set_editor_property('relative_scale3d',unreal.Vector(0.5,0.5,0.5))
mesh.set_collision_profile_name('PhysicsActor')
mesh.set_editor_property('generate_overlap_events',True)
mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
mesh.set_simulate_physics(True)
mesh.set_is_replicated(True)
defaults(carry,replicates=True,replicate_movement=True,net_update_frequency=30.0)
owned(ac)
BP.get_default_object(ac).set_is_replicated(True)
compile_bp(carry); compile_bp(ac)
key=create('/Game/Puzzles/BP_KeyRelic',carry.generated_class())
statue=create('/Game/Puzzles/BP_Statue',carry.generated_class())
for bp in [key,statue]:
    defaults(bp,Heavy=True)
    compile_bp(bp)
out={}
for bp in [carry,ac]:
    g=BP.get_graph(bp,'EventGraph')
    out[bp.get_name()]={term: BP.find_node_types(g,term) for term in ['SetMaxWalkSpeed','CharacterMovement','SetCollision','AttachActor','Detach','AddImpulse','GetComponentByClass','Tags','ClearCarried','Claim','Drop','ReleaseCarried','HasAuthority']}
    out[bp.get_name()]['functions']=[str(x) for x in BP.list_graphs(bp)]
pathlib.Path(__file__).resolve().parents[3].joinpath('Saved/HC4/node_types.json').write_text(__import__('json').dumps(out,default=str,indent=2),encoding='utf-8')
RESULT={'scaffolded':True}
