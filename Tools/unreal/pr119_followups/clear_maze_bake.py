"""Remove the previous maze bake: PlayableMazeScene actors in L_Maze_HZ, then the SM_Maze_* meshes they used."""
import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
editor = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level('/Game/Maps/L_Maze')
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
hz = ue.GameplayStatics.get_streaming_level(world, 'L_Maze_HZ')
assert hz and hz.get_loaded_level()
ue.EditorLevelUtils.make_level_current(hz)
destroyed, other_levels = 0, []
for actor in actors.get_all_level_actors():
    if actor.actor_has_tag('PlayableMazeScene'):
        level = actor.get_level().get_outermost().get_name()
        if level != '/Game/Hazards/L_Maze_HZ':
            other_levels.append([actor.get_actor_label(), level])
            continue
        assert actors.destroy_actor(actor)
        destroyed += 1
assert not other_levels, other_levels
assert ue.EditorLoadingAndSavingUtils.save_packages([hz.get_loaded_level().get_outermost()], False)
registry = ue.AssetRegistryHelpers.get_asset_registry()
meshes = sorted(str(p) for p in ue.EditorAssetLibrary.list_assets('/Game/Puzzles/Art/MazeIntegration/Meshes', False, False))
still_referenced = {}
for path in meshes:
    package = path.split('.')[0]
    refs = [str(r) for r in (registry.get_referencers(package, ue.AssetRegistryDependencyOptions()) or [])]
    if refs:
        still_referenced[package] = refs
assert not still_referenced, still_referenced
deleted = 0
for path in meshes:
    assert ue.EditorAssetLibrary.delete_asset(path.split('.')[0]), path
    deleted += 1
editor.set_current_level_by_name('L_Maze')
RESULT = {'destroyed_scene_actors': destroyed, 'deleted_meshes': deleted}
