import json
import unreal as ue

assert not ue.EditorLevelLibrary.get_pie_worlds(True)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
levels=['/Game/Hazards/L_Maze_HZ','/Game/Player/L_Maze_PG','/Game/Puzzles/L_Maze_HC']
for path in levels:
    if not ue.EditorAssetLibrary.does_asset_exist(path):
        assert editor.new_level(path),path
        assert editor.save_current_level()
map_path='/Game/Maps/L_Maze'
if not ue.EditorAssetLibrary.does_asset_exist(map_path):
    assert editor.new_level(map_path)
else:
    assert editor.load_level(map_path)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()==map_path
world.get_world_settings().set_editor_property('default_game_mode',ue.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
for path in levels:
    existing=ue.GameplayStatics.get_streaming_level(world,path.rsplit('/',1)[-1])
    if not existing:
        result=ue.EditorLevelUtils.add_level_to_world(world,path,ue.LevelStreamingAlwaysLoaded)
        assert result,path
assert editor.set_current_level_by_name('L_Maze')
for a in list(actors.get_all_level_actors()):
    if isinstance(a,ue.PlayerStart) and a.get_level().get_outermost().get_name()!=map_path:
        assert a.get_level().get_outermost().get_name() in levels
        assert actors.destroy_actor(a)
if not [a for a in actors.get_all_level_actors() if isinstance(a,ue.PlayerStart) and a.get_level().get_outermost().get_name()==map_path]:
    for i,y in enumerate([-450,-150,150,450]):
        start=actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(-700,y,100),ue.Rotator(yaw=0))
        assert start.get_level().get_outermost().get_name()==map_path
        start.set_actor_label('MazeStart'+str(i))
assert ue.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
RESULT={'map':map_path,'always_loaded_sublevels':levels,'starts':4}
(QUEUE/'maze-levels.json').write_text(json.dumps(RESULT,indent=2))
