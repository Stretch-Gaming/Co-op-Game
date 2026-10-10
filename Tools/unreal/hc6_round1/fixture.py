"""Owned compact fixture: no production map or art writes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
FOLDER='/Game/Puzzles/Test/HC6'
def new(name,parent):return unreal.load_asset(FOLDER+'/'+name) or BP.create(FOLDER,name,parent)
def fixture_material(name,color):
    mat=unreal.load_asset(FOLDER+'/'+name)
    if not mat:
        mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,FOLDER,unreal.Material,unreal.MaterialFactoryNew())
        exp=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
        exp.set_editor_property('constant',unreal.LinearColor(*color,1))
        assert unreal.MaterialEditingLibrary.connect_material_property(exp,'',unreal.MaterialProperty.MP_BASE_COLOR)
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat
released=fixture_material('M_HC6Released',(.25,.12,.04))
pressed=fixture_material('M_HC6Pressed',(.02,.65,.3))
weight=new('BP_HC6TestWeight',unreal.Actor.static_class())
mesh,h=component(weight,'WeightMesh',unreal.StaticMeshComponent)
mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
mesh.set_editor_property('relative_scale3d',unreal.Vector(.5,.5,.5))
mesh.set_editor_property('relative_location',unreal.Vector(0,0,25))
mesh.set_collision_profile_name('OverlapAllDynamic');mesh.set_editor_property('generate_overlap_events',True)
cdo=BP.get_default_object(weight);cdo.set_editor_property('replicates',True);cdo.set_editor_property('always_relevant',True)
cdo.set_editor_property('tags',['HC_PlateWeight','HC6_FixtureWeight'])
compile_bp(weight);unreal.EditorAssetLibrary.save_loaded_asset(weight)
gm=new('BP_HC6FixtureGameMode',unreal.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
function(gm,'PrepareScaling')
write(gm,'PrepareScaling','''(fn PrepareScaling ()
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (if (Utilities|Enum|Equal(Enum) :A phase :B (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0"))
     (Class|BPCoopGameState|SetRoundState :self gs :RoundState (Utilities|Struct|MakeSRoundState
      :Index_11_91104438409472A6DD374BADC8DC29B1 index
      :Phase_15_0B3D934F45B47D0BD2F25CA01264D4DF phase
      :Attempt_12_246832B34F4E147660E8729696BDD44A attempt
      :PhaseEndsAt_13_75E3D82F49994607AFA23C8B57E08350 ends
      :ScalingRow_14_43C74C304230A92B6620E1A520A230C0
       (Utilities|String|StringToName (Utilities|String|ToString(Integer)
        (Math|Integer|Clamp(Integer) :Value (Class|BPCoopGameState|GetPlayerCount :self gs) :Min 2 :Max 4))))))) (:CastFailed))))''')
BP.add_event(gm,'ReceiveBeginPlay')
write(gm,'EventGraph','''(event EventBeginPlay
 (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "PrepareScaling" :Time 0.2 :bLooping true))''')
compile_bp(gm);unreal.EditorAssetLibrary.save_loaded_asset(gm)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class())
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def spawn(cls,label,location):
    a=sub.spawn_actor_from_class(cls,unreal.Vector(*location),unreal.Rotator())
    a.set_actor_label(label);return a
floor=spawn(unreal.StaticMeshActor,'HC6_FixtureFloor',(0,0,-50))
floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(unreal.Vector(40,40,1))
light=spawn(unreal.DirectionalLight,'HC6_FixtureLight',(0,0,1000));light.set_actor_rotation(unreal.Rotator(-60,0,0),False)
sky=spawn(unreal.SkyLight,'HC6_FixtureSky',(0,0,500))
for i in range(4):spawn(unreal.PlayerStart,'HC6_PlayerStart_'+str(i),(-1000,(i-1.5)*150,100))
plate_bp=unreal.load_asset('/Game/Puzzles/BP_PressurePlate')
for i,xy in enumerate([(400,-450),(400,450),(1200,-450),(1200,450)]):
    a=spawn(plate_bp.generated_class(),'HC6_Plate_'+str(i),(*xy,0))
    a.set_editor_property('PlateSlot',i);a.set_editor_property('tags',['HC_Round1','HC6_Plate_'+str(i)])
    a.set_editor_property('PlateMesh',unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    a.get_component_by_class(unreal.StaticMeshComponent).set_relative_scale3d(unreal.Vector(1.4,1.4,.14))
    a.set_editor_property('ReleasedMaterial',released)
    a.set_editor_property('PressedMaterial',pressed)
setup=spawn(unreal.load_asset('/Game/Puzzles/BP_PuzzleSetup').generated_class(),'HC6_PuzzleSetup',(0,0,0))
setup.set_editor_property('StatueClass',weight.generated_class())
setup.set_editor_property('StatueTransforms',[unreal.Transform(location=unreal.Vector(500,900,0)),unreal.Transform(location=unreal.Vector(800,900,0))])
pad=spawn(unreal.load_asset('/Game/Puzzles/BP_StartPad').generated_class(),'HC6_StartPad',(-300,0,0))
for index,x in [(0,0),(1,1600)]:
    a=spawn(unreal.load_asset('/Game/Puzzles/BP_ChamberGate').generated_class(),'HC6_Gate_'+str(index),(x,0,0))
    a.set_editor_property('RoundIndex',index);a.set_editor_property('tags',['HC6_Gate_'+str(index)])
    a.set_editor_property('GateMesh',unreal.load_asset('/Engine/BasicShapes/Cube'))
    a.get_component_by_class(unreal.StaticMeshComponent).set_relative_scale3d(unreal.Vector(.4,4,4))
assert unreal.EditorLoadingAndSavingUtils.save_map(world,FOLDER+'/L_HC6_Round1')
(OUT/'fixture-build.json').write_text(json.dumps({'project':str(ROOT),'map':FOLDER+'/L_HC6_Round1','game_mode':gm.get_path_name(),'fixture_only':True,'prepared_prop_art_available':False},indent=2))

