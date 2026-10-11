"""Owning headlamp/Q qualification against existing locks. No saved package edits.

Initial approaches and controller aim are fixtures. Inventory authority probes
call RestockFlares locally on a client then the server; they are not RPC proof.
All lamp/throw actions use actual owning Enhanced Input and native RPCs.
"""
import json
import sys
import unreal as ue
sys.path.insert(0, str(HERE))
from harness import Harness
h = Harness(ARGS, 'tools-light')
lock_class = ue.load_asset('/Game/Puzzles/BP_CrystalLock').generated_class()
locks = list(ue.GameplayStatics.get_all_actors_of_class(h.server, lock_class))
beam = next(a for a in locks if not a.get_editor_property('Brazier') and a.get_editor_property('Enabled'))
brazier = next(a for a in locks if a.get_editor_property('Brazier') and a.get_editor_property('Enabled'))
assert h.round()['phase'] == 0, 'Fresh quiet Lobby required'
state = {'owner_index': 0, 'stock': {pid: h.prop(h.pawn(h.server, pid), 'tools', 'FlaresLeft') for pid in h.ids}}
assert all(v == 3 for v in state['stock'].values()), state
observations = []
old_finish = h.finish
def finish(passed, error=None):
    result = old_finish(passed, error)
    if result:
        result['light_observations'] = observations
        h.report.write_text(json.dumps(result, indent=2))
    return result
h.finish = finish

def lock_record(actor):
    return [{'world': w.get_name(), 'lit': bool(h.actor_peer(w, actor).get_editor_property('Lit')),
             'source_count': h.actor_peer(w, actor).get_editor_property('SourceCount')} for w in h.worlds]

def stock(expected):
    for w in h.worlds:
        for p in h.pawns(w):
            assert h.prop(p, 'tools', 'FlaresLeft') == expected[p.player_state.player_id]

def approach(pid, target):
    pos = target.get_actor_location()
    h.fixture_place(pid, [pos.x - 110, pos.y, pos.z + 95])
    h.aims[pid] = target
    h.fixtures.append({'kind': 'maintained owning controller aim', 'id': pid, 'target': target.get_name()})

def tick(_delta):
    elapsed = h.elapsed()
    pid = h.ids[state['owner_index']]
    owner = h.locals[pid]
    tool = h.comp(h.pawn(h.server, pid), 'tools')
    if h.phase == 'warmup':
        if elapsed > 1:
            for other in h.ids:
                if h.prop(h.locals[other], 'view', 'bHeadlampOn'):
                    h.hold(other, 'lamp')
            h.transition('lamps_off')
    elif h.phase == 'lamps_off':
        if elapsed > .2:
            for other in h.ids: h.release(other, 'lamp')
        if elapsed > 1:
            assert all(not h.prop(h.locals[other], 'view', 'bHeadlampOn') for other in h.ids)
            approach(pid, beam)
            h.transition('approach_beam')
    elif h.phase == 'approach_beam' and elapsed > 1:
        h.hold(pid, 'lamp'); h.transition('lamp_on')
    elif h.phase == 'lamp_on':
        if elapsed > .2: h.release(pid, 'lamp')
        if elapsed > 1.5:
            assert tool.get_editor_property('BeamTarget') == beam, 'Server headlamp did not acquire the lock'
            rows = lock_record(beam); assert all(r['lit'] for r in rows), rows
            observations.append({'gate': 'headlamp begin', 'owner': pid, 'rows': rows})
            h.check('owning lamp lights the existing lock on all peers', {'owner': pid})
            h.hold(pid, 'lamp'); h.transition('lamp_off')
    elif h.phase == 'lamp_off':
        if elapsed > .2: h.release(pid, 'lamp')
        if elapsed > 1.5:
            assert tool.get_editor_property('BeamTarget') is None
            rows = lock_record(beam); assert not any(r['lit'] for r in rows), rows
            observations.append({'gate': 'headlamp end', 'owner': pid, 'rows': rows})
            h.check('owning lamp off ends the beam source on all peers', {'owner': pid})
            h.aims.clear(); approach(pid, brazier); h.aims.clear()
            owner.get_controller().set_control_rotation(ue.Rotator(pitch=-90, yaw=0))
            h.fixtures.append({'kind': 'owning downward aim', 'owner': pid, 'pitch': -90})
            h.transition('approach_flare')
    elif h.phase == 'approach_flare':
        owner.get_controller().set_control_rotation(ue.Rotator(pitch=-90, yaw=0))
        if elapsed > 1:
            h.hold(pid, 'flare'); h.transition('throw')
    elif h.phase == 'throw':
        if elapsed > .2: h.release(pid, 'flare')
        if elapsed > 2:
            flares = [a for a in ue.GameplayStatics.get_all_actors_of_class(h.server, h.classes['flare']) if a.get_owner() == h.pawn(h.server, pid)]
            assert len(flares) == 1, ('Expected one native owner flare', len(flares))
            state['flare'] = flares[0]; state['start'] = flares[0].get_editor_property('BurnStarted')
            state['stock'][pid] -= 1; stock(state['stock'])
            assert flares[0].get_editor_property('LightTarget') == brazier, 'Landed native flare did not light the brazier'
            rows = lock_record(brazier); assert all(r['lit'] for r in rows), rows
            observations.append({'gate': 'flare begin', 'owner': pid, 'rows': rows, 'flare_position': str(flares[0].get_actor_location())})
            h.check('native Q lands, spends only owner stock and lights brazier on all peers', {'owner': pid})
            if h.profile == 'joining':
                h.comp(owner, 'tools').call_method('RestockFlares')
                h.fixtures.append({'kind': 'client-local RestockFlares authority probe', 'owner': pid, 'not_rpc': True})
            h.transition('authority_probe')
    elif h.phase == 'authority_probe' and elapsed > .8:
        stock(state['stock'])
        h.check('client-local restock cannot mutate authoritative stock' if h.profile == 'joining' else 'owner stock isolation after native Q', {'owner': pid})
        tool.call_method('RestockFlares')
        state['stock'][pid] = 3
        h.fixtures.append({'kind': 'server-local RestockFlares unit-contract probe', 'owner': pid, 'round_clear_integration_proven': False})
        h.transition('restock')
    elif h.phase == 'restock' and elapsed > .8:
        stock(state['stock']); h.check('server restock restores row-2 allowance on all peers', {'owner': pid})
        h.transition('burn')
    elif h.phase == 'burn':
        age = ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds() - state['start']
        if age > 21:
            rows = lock_record(brazier); assert not any(r['lit'] for r in rows), rows
            assert not ue.SystemLibrary.is_valid(state['flare']), 'Expired flare remains valid'
            observations.append({'gate': 'flare end', 'owner': pid, 'age': age, 'rows': rows})
            h.check('native expiry ends the brazier source on all peers', {'owner': pid})
            state['owner_index'] += 1
            if state['owner_index'] == h.n: h.finish(True)
            else:
                approach(h.ids[state['owner_index']], beam); h.transition('approach_beam')

RESULT = h.register(tick)
