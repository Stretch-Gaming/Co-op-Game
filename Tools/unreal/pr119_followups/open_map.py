import unreal as ue
assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level(ARGS['map'])
RESULT = ARGS['map']
