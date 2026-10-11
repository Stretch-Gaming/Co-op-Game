"""Every blocking hit straight down through each XY spot in the open editor world."""
import unreal as ue
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
out = []
for x, y in ARGS['spots']:
    hits = ue.SystemLibrary.line_trace_multi(world, ue.Vector(x, y, ARGS.get("top", 3000)), ue.Vector(x, y, -6000), ue.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], ue.DrawDebugTrace.NONE, True) or []
    out.append({'spot': [x, y], 'hits': [(round(h.to_tuple()[4].z), h.to_tuple()[9].get_actor_label() if h.to_tuple()[9] else None) for h in hits]})
RESULT = out
