"""Stop only this harness after a Python reporting exception; preserve evidence."""
import gc,types,json,unreal as ue
scopes={id(f.__globals__):f.__globals__ for f in gc.get_objects() if isinstance(f,types.FunctionType) and f.__code__.co_filename.endswith('maze_level\\traversal_runtime.py')}
for scope in scopes.values():
    state=scope['state'];report=scope['report'];report.update(passed=False,phase=state['phase'],error='Harness reporting IndexError after recovery checks; preserved partial evidence')
    (QUEUE/'traversal-runtime-partial-6.json').write_text(json.dumps(report,indent=2))
    ue.unregister_slate_post_tick_callback(state['handle'])
    state['rt'].cleanup_input();ue.get_editor_subsystem(ue.LevelEditorSubsystem).editor_request_end_play()
    scope['OBJ'].set_properties(scope['settings'],json.dumps(scope['old']))
RESULT={'stopped':len(scopes)}
