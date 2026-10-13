"""Read-only active carrier harness progress; no input/state setters."""
import gc,types,json
scopes={id(f.__globals__):f.__globals__ for f in gc.get_objects() if isinstance(f,types.FunctionType) and f.__code__.co_filename.endswith('maze_level\\traversal_runtime.py')}
rows=[]
for s in scopes.values():
    state=s.get('state',{});rt=state.get('rt')
    if state.get('phase') not in ('return','altar','results','restart') or not rt:continue
    p=rt.players[0].get_actor_location();rows.append({'phase':state['phase'],'node':state.get('node'),'nodes':len(s['layout']['return_route']['nodes']),'position':[p.x,p.y,p.z],'round':rt.round(),'held_key':rt.carried(0)==rt.key(),'speed':rt.players[0].character_movement.max_walk_speed})
(QUEUE/'return-progress.json').write_text(json.dumps(rows,indent=2));RESULT=rows
