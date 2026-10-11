"""Sweep a player-sized capsule (r 34, half-height 88) a short way at each spot in the server's PIE world, on the Pawn channel."""
import unreal as ue
worlds = list(ue.EditorLevelLibrary.get_pie_worlds(True)) or [ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()]
world = next((w for w in worlds if ue.GameplayStatics.get_game_mode(w)), worlds[0])
out = []
for x, y, z in ARGS['spots']:
    hit = ue.SystemLibrary.capsule_trace_single(world, ue.Vector(x, y, z), ue.Vector(x, y + 50, z), 34, 88, ue.TraceTypeQuery.TRACE_TYPE_QUERY2, False, [], ue.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    out.append({'spot': [x, y, z], 'blocked': bool(t and t[0]), 'start_penetrating': bool(t and t[1]), 'actor': t[9].get_actor_label() if t and t[0] and t[9] else None})
RESULT = out
