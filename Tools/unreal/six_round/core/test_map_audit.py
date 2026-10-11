"""Read-only editor composition audit after 50_place; no runtime success claim."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
from test_map_contract import *
guard();pg=validate_args(globals().get('ARGS',{}))
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_outermost().get_name()==PERSISTENT
streams={path:ue.GameplayStatics.get_streaming_level(world,path.rsplit('/',1)[-1]) for path in (CAVE_COPY,HC_LEVEL,WORLD_ROUTE,pg)}
assert {level.get_outermost().get_name() for level in ue.EditorLevelUtils.get_levels(world)}=={PERSISTENT,*streams}
assert set(streams)=={CAVE_COPY,HC_LEVEL,WORLD_ROUTE,pg}
assert all(isinstance(s,ue.LevelStreamingAlwaysLoaded) and s.get_loaded_level() for s in streams.values())
assert world.get_world_settings().get_editor_property('default_game_mode')==ue.load_asset(TEST_MODE).generated_class()
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()
assert not [a for a in actors if a.get_class().get_name()=='BP_EnvironmentPreview_C']
doors=[a for a in actors if a.actor_has_tag('ConnectionDoor')];assert len(doors)==1
connection=doors[0];assert connection.get_class()==ue.load_asset(DOOR).generated_class();assert connection.get_level().get_outermost().get_name()==HC_LEVEL
assert (connection.get_actor_location()-ue.Vector(325,1400,200)).length()<1
center,extent=connection.get_actor_bounds(False);assert (center-ue.Vector(325,1400,200)).length()<1
assert abs(extent.x-150)<1 and abs(extent.y-17.5)<1 and abs(extent.z-200)<1
assert not [a for a in actors if a.get_class().get_name()=='BP_EnvironmentDoor_C' or a.get_actor_label()=='Six_MazeDoor']
starts=[a for a in actors if isinstance(a,ue.PlayerStart)];assert len(starts)==4 and all(a.get_level().get_outermost().get_name()==PERSISTENT for a in starts)
checkpoints=[a for a in actors if a.get_class().get_name()=='BP_Checkpoint_C'];assert sorted(a.get_editor_property('RoundIndex') for a in checkpoints)==list(range(7))
assert all(a.get_level().get_outermost().get_name()==HC_LEVEL for a in checkpoints)
assert not [a for a in actors if a.get_level().get_outermost().get_name()==WORLD_ROUTE and a.actor_has_tag('SixRound.TestProxy') and not a.actor_has_tag('SixRound.MantleProbe')]
for path in (TEST_MODE,DOOR):assert ue.load_asset(path).get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
RESULT={'passed':True,'scope':'saved editor composition only','persistent':PERSISTENT,'streamed':sorted(streams),'player_starts':len(starts),'checkpoints':len(checkpoints),'connection_door':connection.get_path_name(),'no_preview_or_duplicate_entrance':True,'runtime_acceptance_pending':True}
QUEUE.mkdir(parents=True,exist_ok=True);(QUEUE/'test-map-audit.json').write_text(json.dumps(RESULT,indent=2))
