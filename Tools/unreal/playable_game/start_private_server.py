import unreal as ue
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ue.SystemLibrary.execute_console_command(world,'ModelContextProtocol.StartServer 8060')
RESULT={'private_server_start_requested':8060}
