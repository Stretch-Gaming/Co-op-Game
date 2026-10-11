"""PIE check for the re-applied cave traps (run with _during_pie while Play As Client is running on L_Site01).

Checks that every trap exists on the server and every client with the same replicated schedule, then moves
one player onto the darts and another onto the spikes on the server, and checks that the damage lands on
the server and replicates to the clients, and that a client sees the spike warning before it fires.
Writes Saved/PR119/cave-traps.json.
"""
import json
import time
import traceback
import unreal as ue

REPORT = QUEUE / 'cave-traps.json'
TRAP = ue.load_asset('/Game/Hazards/Traps/BP_AdventureTrap').generated_class()
FALL = ue.load_asset('/Game/Hazards/Traps/BP_FallVolume').generated_class()
CHARACTER = ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
HEALTH = ue.load_asset('/Game/Hazards/AC_Health').generated_class()
SCHEDULE = ('Kind', 'StartTime', 'Interval', 'SpikeDelay', 'SwingSpeed')

worlds = list(ue.EditorLevelLibrary.get_pie_worlds(True))
server = next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
clients = [w for w in worlds if w != server]
state = {'phase': 0, 'start': time.monotonic(), 'deadline': time.monotonic() + 60 + ARGS.get('join_wait', 17), 'checks': [], 'data': {}}

def by_label(world):
    return {round(a.get_actor_location().x) * 100000 + round(a.get_actor_location().y): a for a in ue.GameplayStatics.get_all_actors_of_class(world, TRAP)}

def health_of(pawn):
    return pawn.get_component_by_class(HEALTH).get_editor_property('Health')

def same_pawn_in(world, pawn):
    pid = pawn.get_editor_property('player_state').get_editor_property('player_id')
    return next(p for p in ue.GameplayStatics.get_all_actors_of_class(world, CHARACTER) if p.get_editor_property('player_state') and p.get_editor_property('player_state').get_editor_property('player_id') == pid)

def finish(passed, error=None):
    ue.unregister_slate_post_tick_callback(state['handle'])
    REPORT.write_text(json.dumps({'passed': passed, 'error': error, 'checks': state['checks'], 'data': state['data'], 'phase': state['phase']}, indent=2, default=str))

def transition(phase):
    state['phase'] = phase
    state['start'] = time.monotonic()

def tick(delta):
    try:
        assert time.monotonic() < state['deadline'], 'test exceeded its deadline'
        elapsed = time.monotonic() - state['start']
        phase = state['phase']
        if phase == 0 and elapsed > 2:
            server_traps = by_label(server)
            assert len(server_traps) == 9, len(server_traps)
            assert len(ue.GameplayStatics.get_all_actors_of_class(server, FALL)) == 1
            mismatches = []
            for client in clients:
                client_traps = by_label(client)
                assert set(client_traps) == set(server_traps), 'client is missing traps'
                for key, trap in server_traps.items():
                    for prop in SCHEDULE:
                        a, b = trap.get_editor_property(prop), client_traps[key].get_editor_property(prop)
                        if abs(a - b) >= 1e-3:
                            mismatches.append((key, prop, a, b))
            # Placed traps exist on a joining client before their replicated schedule arrives; wait for it
            # (4-client PIE runs at about 12 fps on one Mac, so joining is slow).
            if mismatches:
                if elapsed > ARGS.get('join_wait', 17):
                    lagging = [c.get_name() + ':' + str(len(ue.GameplayStatics.get_all_actors_of_class(c, CHARACTER))) + ' pawns' for c in clients if any(abs(t.get_editor_property('StartTime') - server_traps[k].get_editor_property('StartTime')) >= 1e-3 for k, t in by_label(c).items())]
                    raise AssertionError(('schedule never replicated', mismatches[:4], lagging))
                return
            state['data']['schedule_replicated_after_s'] = round(elapsed, 1)
            sample = next(iter(server_traps.values()))
            state['data']['scaling_row'] = str(sample.get_editor_property('ScalingRow'))
            state['data']['schedule'] = {str(k): {p: round(t.get_editor_property(p), 3) for p in SCHEDULE} for k, t in sorted(server_traps.items())}
            state['checks'].append('9 traps and the fall volume exist on the server; every client has every trap with the same replicated schedule')
            players = list(ue.GameplayStatics.get_all_actors_of_class(server, CHARACTER))
            assert len(players) == len(clients), (len(players), len(clients))
            assert state['data']['scaling_row'] == str(len(players)), ('scaling row', state['data']['scaling_row'], len(players))
            state['checks'].append(f'{len(players)} players; every trap reads DT_HazardScaling row {len(players)}')
            state['dart_player'], state['spike_player'] = players[:2]
            state['dart_start'] = health_of(players[0])
            state['spike_start'] = health_of(players[1])
            players[0].set_actor_location(ue.Vector(6200, 0, 100), False, True)
            players[1].set_actor_location(ue.Vector(2000, 0, 100), False, True)
            state['spike_trap'] = {c: by_label(c)[2000 * 100000] for c in clients}
            state['warning_seen'] = False
            transition(1)
        elif phase == 1:
            state.setdefault('frames', 0)
            state['frames'] += 1
            server_spike = by_label(server)[2000 * 100000]
            for c, t in state['spike_trap'].items():
                key = 'trigger_lag_' + c.get_name() + str(clients.index(c))
                if key not in state['data'] and t.get_editor_property('TriggeredAt') > 0 and abs(t.get_editor_property('TriggeredAt') - server_spike.get_editor_property('TriggeredAt')) < 1e-3:
                    state['data'][key] = round(t.get_editor_property('Now') - t.get_editor_property('TriggeredAt'), 3)
            if any(t.get_editor_property('Warning') for t in state['spike_trap'].values()):
                if not state['warning_seen']:
                    state['warning_seen'] = True
                    state['data']['spike_health_when_client_warned'] = health_of(state['spike_player'])
            darts_hit = health_of(state['dart_player']) < state['dart_start']
            spikes_hit = health_of(state['spike_player']) < state['spike_start']
            if darts_hit and spikes_hit and elapsed > 0.5:
                state['data']['spike_delay'] = round(server_spike.get_editor_property('SpikeDelay'), 3)
                state['data']['editor_fps'] = round(state['frames'] / max(elapsed, 1e-3), 1)
                state['data']['server_health_after'] = {'darts': health_of(state['dart_player']), 'spikes': health_of(state['spike_player'])}
                assert state['warning_seen'], 'no client saw the spike warning'
                assert state['data']['spike_health_when_client_warned'] == state['spike_start'], 'spikes hit before the client warning'
                state['checks'].append('server applies dart and spike damage; a client shows the spike warning before the hit')
                # Step off the traps so no later volley changes health while the clients catch up.
                state['dart_player'].set_actor_location(ue.Vector(500, -150, 100), False, True)
                state['spike_player'].set_actor_location(ue.Vector(500, 150, 100), False, True)
                transition(2)
            elif elapsed > 15:
                raise AssertionError(f'no damage within 15 s: darts {darts_hit}, spikes {spikes_hit}')
        elif phase == 2 and elapsed > 0.5:
            stale = [(key, health_of(same_pawn_in(client, state[key])), health_of(state[key])) for client in clients for key in ('dart_player', 'spike_player')
                     if abs(health_of(same_pawn_in(client, state[key])) - health_of(state[key])) >= 1e-3]
            if stale:
                assert elapsed < 5, ('health not replicated within 5 s', stale)
                return
            state['data']['server_health_final'] = {'darts': health_of(state['dart_player']), 'spikes': health_of(state['spike_player'])}
            state['checks'].append(f'damaged health replicates to all {len(clients)} clients')
            finish(True)
    except Exception:
        finish(False, traceback.format_exc())

state['handle'] = ue.register_slate_post_tick_callback(tick)
RESULT = {'queued': str(REPORT)}
