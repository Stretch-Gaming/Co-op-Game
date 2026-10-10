import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
ue.SystemLibrary.execute_console_command(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(),'QUIT_EDITOR')
