"""Place only PG actors in the isolated PG test streaming map. Primary runs."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from authoring import *
guard()
target='/Game/Player/Test/SixRound/L_SixRound_PG_Test'
assert ARGS.get('target_map',target)==target,'Only the isolated PG test map is authorized'
layout=json.loads((ROOT/'Tools/unreal/six_round/world/positions.json').read_text())
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
if not ue.EditorAssetLibrary.does_asset_exist(target):
 assert editor.new_level(target);assert editor.save_current_level()
else:assert editor.load_level(target)
assert editor.set_current_level_by_name(target.rsplit('/',1)[-1])
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()==target
tag='SixRoundPGTest'
for actor in actors.get_all_level_actors():
 if actor.actor_has_tag(tag):
  assert actor.get_level().get_outermost().get_name()==target
  assert actors.destroy_actor(actor)
written=[]
def spawn(path,label,position,tags=(),compile_asset=True):
 bp=ue.load_asset(path);assert bp,path
 if compile_asset:compile_bp(bp)
 actor=actors.spawn_actor_from_class(bp.generated_class(),ue.Vector(*position),ue.Rotator())
 assert actor and actor.get_level().get_outermost().get_name()==target
 actor.set_actor_label(label);actor.set_folder_path('SixRound/Player')
 actor.set_editor_property('tags',[ue.Name(tag),*[ue.Name(value) for value in tags]])
 written.append({'label':label,'class':path,'position':list(position),'package':target})
 return actor
taking=spawn('/Game/Player/Taking/BP_TakingDirector','Six_TakingDirector',layout['maze_mouth']['center'])
for slot,position in enumerate(layout['first_path_starts']):
 taking.set_editor_property('PathStart'+str(slot),ue.Vector(*position))
cage=spawn('/Game/Player/RelicChamber/BP_RelicCage','Six_RelicCage',layout['relic']['cage'],['RelicCage'])
meshes=cage.get_components_by_class(ue.StaticMeshComponent)
assert meshes,'Cage must have its authored moving collision mesh'
for mesh in meshes:mesh.set_collision_profile_name('BlockAllDynamic')
for slot,position in enumerate(layout['relic']['levers']):
 lever=spawn('/Game/Player/RelicChamber/BP_Lever','Six_RelicLever_'+str(slot),position)
 assert ue.SystemLibrary.does_implement_interface(lever,ue.load_asset('/Game/Core/BPI_Interactable').generated_class())
 assert ue.SystemLibrary.does_implement_interface(lever,ue.load_asset('/Game/Core/BPI_RoundReset').generated_class())
spawn('/Game/Player/Ghosts/BP_ChaseDirector','Six_ChaseDirector',layout['relic']['escape_ledge'])
round_ghost_path='/Game/Player/Ghosts/BP_RoundGhostDirector'
round_ghosts_placed=bool(ue.load_asset(round_ghost_path))
if round_ghosts_placed:
 director=spawn(round_ghost_path,'Six_RoundGhostDirector',[0,0,0],['SixRound.RoundGhostDirector'])
 for stage,key in [('First','first_routes'),('Second','second_routes')]:
  for route in layout[key]:
   point=list(route['nodes'][-2]);point[2]+=100
   director.set_editor_property(stage+'Threat'+str(route['ColorSlot']),ue.Vector(*point))
 for index,center in [(1,[0,0,0]),(3,layout['meeting']['center']),(5,layout['relic']['center'])]:
  for side in (0,1):director.set_editor_property('Room'+str(index)+'Threat'+str(side),ue.Vector(center[0]+(-1000 if side==0 else 1000),center[1]+650,center[2]+100))
zipline=spawn('/Game/Player/Zipline/BP_Zipline','Six_EscapeZipline',layout['relic']['escape_ledge'],['SixRound.EscapeZipline'],compile_asset=False)
zipline_bp=ue.load_asset('/Game/Player/Zipline/BP_Zipline')
zipline_contract={'variables':list(BP.list_variables(zipline_bp)),'start':layout['relic']['escape_ledge'],'landing':layout['exit_ledge'],'configured':False}
# EndPoint is present in the existing serialized asset name table. Inspect its
# actual reflected type here rather than inventing a new property or class.
end=zipline.get_editor_property('EndPoint')
zipline_contract['end_property_type']=type(end).__name__
local_end=ue.Vector(*(layout['exit_ledge'][i]-layout['relic']['escape_ledge'][i] for i in range(3)))
if isinstance(end,ue.SceneComponent):
 end.set_relative_location(local_end,False,False);zipline_contract['configured']=True;zipline_contract['space']='component-local'
elif isinstance(end,ue.Vector) and ARGS.get('zipline_end_space') in ('local','world'):
 zipline.set_editor_property('EndPoint',local_end if ARGS['zipline_end_space']=='local' else ue.Vector(*layout['exit_ledge']))
 zipline_contract['configured']=True;zipline_contract['space']=ARGS['zipline_end_space']
else:
 zipline_contract['pending']='Primary must inspect EndPoint type/coordinate space and provide zipline_end_space or tune actor instance; existing zipline class is unchanged'
for actor in (taking,cage):
 assert ue.SystemLibrary.does_implement_interface(actor,ue.load_asset('/Game/Core/BPI_RoundReset').generated_class())
assert ue.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
RESULT={'map':target,'writes':[target],'actors':written,'round_ghosts_placed':round_ghosts_placed,'zipline':zipline_contract,'placed_references':'None; cage/lever/relic/seal contracts found at runtime','collision':'PG cage mesh BlockAllDynamic; HZ owns floors/climbable overlap shafts and zipline landing floor','runtime_acceptance_pending':True}
(QUEUE/'pg-test-placement.json').write_text(json.dumps(RESULT,indent=2))
