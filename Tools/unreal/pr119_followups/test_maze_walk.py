"""Play As Client on L_Maze: put every player inside the maze at ARGS['spot'] on the server, then drive each
client's real Enhanced Input (IA_Move injected every frame on every client subsystem) and check that every
player moves on the server and stays on the ground. Writes Saved/PR119/maze-walk.json."""
import json, time, traceback
import unreal as ue
CHARACTER = ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
MOVE = ue.load_asset('/Game/Input/Actions/IA_Move')
worlds = list(ue.EditorLevelLibrary.get_pie_worlds(True))
server = next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
library = ue.load_object(None, '/Script/Engine.Default__SubsystemBlueprintLibrary')
local_pawns = [p for w in worlds if w != server for p in ue.GameplayStatics.get_all_actors_of_class(w, CHARACTER) if p.is_locally_controlled()]
subsystems = [library.call_method('GetLocalPlayerSubSystemFromPlayerController', args=(p.get_controller(), ue.EnhancedInputLocalPlayerSubsystem.static_class())) for p in local_pawns]
assert len(subsystems) == len(worlds) - 1 and all(subsystems), subsystems
players = list(ue.GameplayStatics.get_all_actors_of_class(server, CHARACTER))
x, y, z = ARGS['spot']
for i, p in enumerate(players):
    p.set_actor_location(ue.Vector(x + (i - 1.5) * 120, y, z), False, True)
state = {'start': time.monotonic(), 'phase': 0}
report = QUEUE / 'maze-walk.json'
def finish(data):
    ue.unregister_slate_post_tick_callback(state['h'])
    report.write_text(json.dumps(data, indent=2, default=str))
def tick(delta):
    try:
        t = time.monotonic() - state['start']
        if state['phase'] == 0 and t > 1.5:
            state['before'] = [p.get_actor_location() for p in players]
            state['phase'] = 1
        elif state['phase'] == 1:
            for s in subsystems:
                s.inject_input_vector_for_action(MOVE, ue.Vector(0, 1, 0), [], [])
            if t > 3.5:
                rows = []
                for p, b in zip(players, state['before']):
                    l = p.get_actor_location()
                    rows.append({'moved_cm': round((l - b).length()), 'z': round(l.z), 'on_ground': p.get_component_by_class(ue.CharacterMovementComponent).is_moving_on_ground()})
                finish({'passed': all(r['moved_cm'] > 100 and r['on_ground'] for r in rows), 'players': rows, 'subsystems': len(subsystems)})
    except Exception:
        finish({'passed': False, 'error': traceback.format_exc()})
state['h'] = ue.register_slate_post_tick_callback(tick)
RESULT = {'players': len(players), 'subsystems': len(subsystems)}
