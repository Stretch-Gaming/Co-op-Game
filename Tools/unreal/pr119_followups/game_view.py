import unreal as ue
ue.get_editor_subsystem(ue.LevelEditorSubsystem).editor_set_game_view(ARGS.get('on', True))
RESULT = 'ok'
