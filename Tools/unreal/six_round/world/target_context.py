"""Temporary HZ test staging. Production packages owned by PK are never writable."""
import unreal as ue
TEST_MAP='/Game/Hazards/Test/SixRound/L_WorldRoute_Test'
def open_target(args):
    target=args.get('target_map',TEST_MAP)
    assert target==TEST_MAP,'Production integration needs PK delivery; only the new HZ test map is authorized'
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
    if not ue.EditorAssetLibrary.does_asset_exist(target):
        assert editor.new_level(target)
        assert editor.save_current_level()
    else:assert editor.load_level(target)
    assert editor.set_current_level_by_name(target.rsplit('/',1)[-1])
    world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_name()==target
    return world,world.get_outermost(),target
