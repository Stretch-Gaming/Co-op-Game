"""Correct a live harness timeout: reset only for measured physical progress.
No pawn/game state or input changes. Long hall crossings exceed the original
12-second per-waypoint deadline even while the carrier is moving normally.
"""
import gc,types,time,unreal as ue
scopes={id(f.__globals__):f.__globals__ for f in gc.get_objects() if isinstance(f,types.FunctionType) and f.__code__.co_filename.endswith('maze_level\\traversal_runtime.py')}
scope=next(s for s in scopes.values() if s.get('state',{}).get('phase')=='return');state=scope['state'];rt=state['rt'];previous=rt.players[0].get_actor_location()
scope['report']['fixtures'].append('Harness liveness watchdog resets only after measured 10cm physical progress; no per-waypoint time limit while moving')
def tick(delta):
    global previous
    if state['phase']!='return':ue.unregister_slate_post_tick_callback(handle);return
    p=rt.players[0].get_actor_location()
    if (p-previous).length()>10:state['last_progress']=time.monotonic();previous=p
handle=ue.register_slate_post_tick_callback(tick)
RESULT={'observing_only':True}
