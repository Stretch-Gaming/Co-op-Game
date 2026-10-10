"""PIE gravity/overlap death gate; initial airborne placement is a disclosed fixture."""
import importlib.util,json
from pathlib import Path
import unreal as ue
world_dir=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('six_round_chasm_harness',world_dir.parent/'player/tests/common.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
h=native.Harness(ARGS,'world-chasm')
assert 'player_id' in ARGS and ARGS['player_id'] in h.ids
pid=ARGS['player_id'];pawn=h.pawn(h.server,pid)
assert not h.prop(pawn,'health','bDead') and h.round()['phase']==1
layout=json.loads((world_dir/'positions.json').read_text())
region=layout['deadly_chasms'][0]
# Off the guarded bridge, inside the visible chasm bounds. Gravity and the real
# overlap trigger do the work; no damage/death/gameplay reset method is called.
h.fixture_place(pid,[region['center'][0]+region['extent'][0]-100,region['center'][1],300])
h.fixtures[-1]['kind']='initial airborne chasm fixture; natural gravity follows'
h.transition('falling')
def tick(delta):
    if h.phase=='falling' and h.prop(pawn,'health','bDead'):
        current=pawn.get_actor_location();assert current.z<layout['round6_bounds']['chasm_overlap_z_max']+200
        h.transition('death_replication')
    elif h.phase=='death_replication' and h.elapsed()>.8:
        for world in h.worlds:
            peer=h.pawn(world,pid);assert h.prop(peer,'health','bDead')
        h.check('natural gravity entered SixRound chasm and authoritative death replicated',{'kill_top_z':layout['round6_bounds']['chasm_overlap_z_max'],'key_lost_threshold':layout['round6_bounds']['key_lost_z_threshold'],'initial_airborne_fixture':True,'walking_off_guardrails_tested':False})
        h.finish(True)
RESULT=h.register(tick)
