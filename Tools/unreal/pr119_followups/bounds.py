"""Bounds of actors whose label contains any of ARGS['match']."""
import unreal as ue
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
out = []
for a in actors.get_all_level_actors():
    if any(m in a.get_actor_label() for m in ARGS['match']):
        o, e = a.get_actor_bounds(False)
        out.append([a.get_actor_label(), a.get_level().get_outermost().get_name().rsplit('/',1)[-1], [round(o.x - e.x), round(o.y - e.y), round(o.z - e.z)], [round(o.x + e.x), round(o.y + e.y), round(o.z + e.z)]])
RESULT = sorted(out)
