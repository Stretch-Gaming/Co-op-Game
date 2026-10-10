"""Transient PIE fixtures; only injected Enhanced Input exercises gameplay RPCs."""
import json
from pathlib import Path
import time
import traceback
import unreal

ROOT = Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == ROOT / 'CoopGame.uproject'
QUEUE = ROOT / 'Saved/PGSignatureFix'
opts = json.loads((QUEUE / 'options.json').read_text(encoding='utf-8-sig'))
worlds = unreal.EditorLevelLibrary.get_pie_worlds(True)
server = next(w for w in worlds if unreal.GameplayStatics.get_game_mode(w))
if opts.get('split'):
    assert unreal.GameplayStatics.create_player(server, -1, True)
character = unreal.load_asset('/Game/Player/Test/BP_PG_TestCharacter').generated_class()
probe_class = unreal.load_asset('/Game/Puzzles/Test/BP_TestInteractable').generated_class()
action = unreal.load_asset('/Game/Player/Test/IA_PG_Interact')
test_context = unreal.load_asset('/Game/Player/Test/IMC_PG_Test')
core_context = unreal.load_asset('/Game/Core/Input/IMC_Coop')
expected_players = opts['players'] + (1 if opts.get('split') else 0)
state = {'phase': 'owners', 'start': time.monotonic(), 'deadline': time.monotonic() + 45,
         'history': [], 'owners': [], 'probes': [], 'checks': 0}
def require(value, message):
    state['checks'] += 1
    assert value, message
def pawns(world):
    return unreal.GameplayStatics.get_all_actors_of_class(world, character)
def probes(world):
    return unreal.GameplayStatics.get_all_actors_of_class(world, probe_class)
def input_subsystem(pawn):
    library = unreal.get_default_object(unreal.load_class(None, '/Script/Engine.SubsystemBlueprintLibrary'))
    return library.call_method('GetLocalPlayerSubsystem', args=(pawn, unreal.EnhancedInputLocalPlayerSubsystem.static_class()))
def has_context(sub, context):
    result = sub.has_mapping_context(context)
    # UE's Python binding returns the found priority on success, including 0,
    # and None on failure for this bool-plus-output-parameter function.
    return result is not None and (result >= 0 if isinstance(result, int) else bool(result))
def snapshot():
    return [{'world': w.get_path_name(), 'server': w == server,
             'players': len(pawns(w)),
             'probes': [{'name': p.get_name(), 'instant': p.get_editor_property('InstantCount'),
                         'begin': p.get_editor_property('BeginCount'), 'end': p.get_editor_property('EndCount'),
                         'active': p.get_editor_property('ActiveUsers')} for p in probes(w)]} for w in worlds]
def mode(index):
    # Configure the transient fixture metadata consistently on every peer.
    # No gameplay counters, gameplay functions or RPCs are called here.
    for w in worlds:
        for p in probes(w):
            p.set_editor_property('Mode', type(p.get_editor_property('Mode')).cast(index))
            p.set_editor_property('HoldSeconds', 0.5)
def inject(value):
    for pawn, sub in state['owners']:
        sub.inject_input_vector_for_action(action, unreal.Vector(value, 0, 0), [], [])
def transition(name):
    state['phase'] = name
    state['start'] = time.monotonic()
def check_counts(instant, begin=0, end=0):
    rows = snapshot()
    for row in rows:
        require(row['players'] == expected_players, 'Player count on ' + row['world'])
        require(len(row['probes']) == expected_players, 'Replicated probe count on ' + row['world'])
        for p in row['probes']:
            require((p['instant'], p['begin'], p['end'], p['active']) == (instant, begin, end, 0),
                    (state['phase'], row['world'], p))
    state['history'].append({'phase': state['phase'], 'worlds': rows})
def finish(passed, error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report = {'passed': passed, 'error': error, 'players': expected_players, 'split': bool(opts.get('split')),
              'checks': state['checks'], 'owners': [p.get_path_name() for p, _ in state['owners']],
              'history': state['history'], 'final': snapshot()}
    (QUEUE / ('input-' + ('split' if opts.get('split') else str(expected_players)) + '.json')).write_text(json.dumps(report, indent=2))
def tick(_delta):
    try:
        now = time.monotonic()
        if now >= state['deadline']:
            raise AssertionError('Runtime test timed out')
        phase, elapsed = state['phase'], now - state['start']
        if phase == 'owners' and elapsed > 1:
            if any(len(pawns(w)) != expected_players for w in worlds):
                return
            locals_ = [(p, input_subsystem(p))
                       for w in worlds for p in pawns(w) if p.is_locally_controlled()]
            require(len(locals_) == expected_players, 'One input owner per player')
            for p, sub in locals_:
                require(sub is not None, 'Owning Enhanced Input subsystem')
                require(p.get_editor_property('InputReady'), 'Parent input setup ran')
                require(has_context(sub, test_context), 'PG context belongs to owner')
                require(has_context(sub, core_context), 'Core context belongs to owner')
                widget = p.get_editor_property('PromptWidget')
                require(widget and widget.get_owning_player() == p.get_controller(), 'Prompt belongs to owner')
            state['owners'] = locals_
            for index, p in enumerate(sorted(pawns(server), key=lambda p: p.player_state.get_editor_property('player_id'))):
                p.set_actor_location(unreal.Vector(0, index * 600, 100), False, True)
            transition('place')
        elif phase == 'place' and elapsed > 0.7:
            for p, _ in state['owners']:
                camera = p.get_component_by_class(unreal.CameraComponent)
                position = camera.get_world_location() + camera.get_forward_vector() * 200
                transform = unreal.Transform(location=position)
                statics = unreal.get_default_object(unreal.GameplayStatics.static_class())
                probe = statics.call_method('BeginDeferredActorSpawnFromClass', args=(server, probe_class, transform,
                    unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN, None, unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
                require(probe is not None, 'Transient server fixture spawned')
                probe.set_editor_property('HoldSeconds', 0.5)
                statics.call_method('FinishSpawningActor', args=(probe, transform, unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
                state['probes'].append(probe)
            transition('focus')
        elif phase == 'focus' and elapsed > 1:
            for p, _ in state['owners']:
                target = p.get_editor_property('FocusedTarget')
                require(target and target.get_class() == probe_class, 'Native camera trace acquired fixture')
            mode(0)
            transition('instant')
        elif phase == 'instant':
            inject(1 if elapsed < 0.15 else 0)
            if elapsed > 0.65:
                check_counts(1)
                mode(1)
                transition('cancel')
        elif phase == 'cancel':
            inject(1 if elapsed < 0.15 else 0)
            if elapsed > 0.65:
                check_counts(1)
                transition('timed')
        elif phase == 'timed':
            inject(1 if elapsed < 0.9 else 0)
            if elapsed > 1.4:
                check_counts(2)
                mode(2)
                transition('continuous')
        elif phase == 'continuous':
            inject(1 if elapsed < 0.3 else 0)
            if elapsed > 0.8:
                check_counts(2, 1, 1)
                require(all(not p.get_editor_property('InputHeld') for p, _ in state['owners']), 'Local input released')
                finish(True)
    except Exception:
        inject(0)
        finish(False, traceback.format_exc())
state['handle'] = unreal.register_slate_post_tick_callback(tick)
RESULT = {'scheduled': True, 'players': expected_players}
