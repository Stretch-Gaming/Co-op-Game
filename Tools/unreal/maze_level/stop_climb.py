"""Stop a disconnected diagnostic callback and preserve its partial results."""
import gc,types,json,unreal as ue
scopes={id(f.__globals__):f.__globals__ for f in gc.get_objects() if isinstance(f,types.FunctionType) and f.__code__.co_filename.endswith('maze_level\\climb_live.py')}
for scope in scopes.values():
    try:ue.unregister_slate_post_tick_callback(scope['state']['handle'])
    except Exception:pass
    scope['report'].update(passed=False,error='Carrier guide fixture ended PIE during independent mantle check')
    (QUEUE/'climb-partial-1.json').write_text(json.dumps(scope['report'],indent=2))
RESULT={'stopped':len(scopes)}
