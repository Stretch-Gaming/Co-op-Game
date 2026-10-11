"""Assemble only new test levels. Copy delivered cave; stream full WorldRoute
once. Do not stream ConnectedMaze or any production gameplay sublevel.
"""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
from test_map_contract import *
guard();args=globals().get('ARGS',{});pg=validate_args(args)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
for path in (CAVE_SOURCE,WORLD_ROUTE,pg,TEST_MODE,DOOR):assert ue.EditorAssetLibrary.does_asset_exist(path),f'Author prerequisite first: {path}'
# File hashes are evidence only, never used to edit binary files.
protected_files=[ROOT/'Content/Hazards/L_Site01_HZ.umap',ROOT/'Content/Puzzles/EnvironmentConnection/BP_EnvironmentDoor.uasset',ROOT/'Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap']
protected_before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected_files}
copy_file=ROOT/'Content/Puzzles/Test/SixRound/L_CaveEnvironment_Test.umap'
if not copy_file.is_file():
 # Generic asset duplication does not persist a World in this engine build.
 # Save the read-only source World under the exact new package, then load it.
 assert editor.load_level(CAVE_SOURCE)
 source_world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
 assert source_world.get_outermost().get_name()==CAVE_SOURCE
 assert ue.EditorLoadingAndSavingUtils.save_map(source_world,CAVE_COPY)
 assert copy_file.is_file()
 assert {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected_files}==protected_before
for path in (HC_LEVEL,PERSISTENT):
 if not ue.EditorAssetLibrary.does_asset_exist(path):
  assert editor.new_level(path);assert editor.save_current_level()
assert editor.load_level(PERSISTENT)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_outermost().get_name()==PERSISTENT
writable_package(world.get_outermost())
world.get_world_settings().set_editor_property('default_game_mode',ue.load_asset(TEST_MODE).generated_class())
allowed={CAVE_COPY,HC_LEVEL,WORLD_ROUTE,pg}
loaded_names=lambda:{level.get_outermost().get_name() for level in ue.EditorLevelUtils.get_levels(world)}
assert loaded_names()<={PERSISTENT,*allowed},'Refuse unexpected loaded level'
for path in (CAVE_COPY,HC_LEVEL,WORLD_ROUTE,pg):
 stream=ue.GameplayStatics.get_streaming_level(world,path.rsplit('/',1)[-1])
 if not stream:stream=ue.EditorLevelUtils.add_level_to_world(world,path,ue.LevelStreamingAlwaysLoaded)
 assert stream,path
 ue.GameplayStatics.flush_level_streaming(world)
 assert stream and stream.get_loaded_level().get_outermost().get_name()==path
 assert isinstance(stream,ue.LevelStreamingAlwaysLoaded),f'Always-loaded required: {path}'
assert loaded_names()=={PERSISTENT,*allowed}
# Clean only the owned cave copy. Never load/save the source cave as an editor target.
cave=ue.GameplayStatics.get_streaming_level(world,CAVE_COPY.rsplit('/',1)[-1]);assert cave.get_loaded_level()
package=cave.get_loaded_level().get_outermost();writable_package(package)
removed=[];straddles=[]
for actor in list(actors.get_all_level_actors()):
 if actor.get_level().get_outermost().get_name()!=CAVE_COPY:continue
 safe_actor(actor,package)
 name=actor.get_class().get_name();label=actor.get_actor_label();origin,extent=actor.get_actor_bounds(False)
 preview=name=='BP_EnvironmentPreview_C' or label=='Environment_Preview'
 lower=name.lower()
 gameplay=isinstance(actor,(ue.PlayerStart,ue.Pawn)) or name.startswith(('BP_EnvironmentDoor','BP_PuzzleConnectionDoor')) or any(token in lower for token in ('trap','ghost','checkpoint','zipline','mapexit','testinteract','gauntlet','carryable','statue','relic','pressureplate','puzzlesetup','rounddirector','roundstart','regroup','startpad','chambergate','mazemover','mouthseal','lever','cage','fallvolume'))
 wholly_north=origin.y-extent.y>=3200
 if preview or gameplay or wholly_north:
  removed.append({'label':label,'class':name});assert actors.destroy_actor(actor)
 elif origin.y+extent.y>3200:
  straddles.append({'label':label,'class':name,'origin':[origin.x,origin.y,origin.z],'extent':[extent.x,extent.y,extent.z]})
# WorldRoute must be authored with include_test_cave_proxies=false before composition.
assert not [a for a in actors.get_all_level_actors() if a.get_level().get_outermost().get_name()==WORLD_ROUTE and a.actor_has_tag('SixRound.TestProxy') and not a.actor_has_tag('SixRound.MantleProbe')],'Rebuild WorldRoute with include_test_cave_proxies=false'
assert not [a for a in actors.get_all_level_actors() if a.get_class().get_name()=='BP_EnvironmentPreview_C'],'No EnvironmentPreview may run in the composite test'
assert not [a for a in actors.get_all_level_actors() if a.get_class().get_name()=='BP_EnvironmentDoor_C'],'No standalone manual door may remain in the composite test'
for a in actors.get_all_level_actors():
 if a.actor_has_tag('ConnectionDoor'):
  assert a.get_class().get_path_name()==DOOR+'.BP_PuzzleConnectionDoor_C' and a.get_level().get_outermost().get_name()==HC_LEVEL
assert len([a for a in actors.get_all_level_actors() if a.actor_has_tag('ConnectionDoor')])<=1
assert editor.set_current_level_by_name(PERSISTENT.rsplit('/',1)[-1])
for a in list(actors.get_all_level_actors()):
 if a.get_level().get_outermost().get_name()==PERSISTENT and isinstance(a,ue.PlayerStart):safe_actor(a,world.get_outermost());assert actors.destroy_actor(a)
layout=json.loads((ROOT/'Tools/unreal/six_round/world/positions.json').read_text())
for slot,pos in enumerate(layout['spawn_spots']):
 a=actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(*pos),ue.Rotator(yaw=90));safe_actor(a,world.get_outermost());a.set_actor_label('Six_TestStart_'+str(slot));a.tags=[ue.Name('SixRoundTest.Persistent'),ue.Name('ColorSlot'+str(slot))]
saved=save_exact(ue,[package,world.get_outermost()])
protected_after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected_files};assert protected_after==protected_before,'Source binary changed'
RESULT={'persistent':PERSISTENT,'hc':HC_LEVEL,'cave_copy':CAVE_COPY,'streamed':sorted(allowed),'saved':saved,'source_hashes':protected_after,'copied_cave_actors_removed':removed,'north_boundary_straddles_to_inspect':straddles,'remaining_runtime_tests':['2/3/4 client + split round gates','sole closed/open connection collision','six-round route + death/wipe + regroup','results game-override travel and native host restart'],'runtime_acceptance_pending':True}
QUEUE.mkdir(parents=True,exist_ok=True);(QUEUE/'test-map-assembly.json').write_text(json.dumps(RESULT,indent=2))
