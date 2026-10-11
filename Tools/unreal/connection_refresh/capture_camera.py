import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
assert ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world().get_outermost().get_name()=='/Game/Maps/L_ConnectedRoomMaze'
ue.EditorLevelLibrary.set_level_viewport_camera_info(ue.Vector(325,3250,220),ue.Rotator(yaw=90))
if hasattr(ue.EditorLevelLibrary,'editor_set_game_view'):ue.EditorLevelLibrary.editor_set_game_view(True)
RESULT={'camera':'maze fork scenery review only; no actor changes'}
