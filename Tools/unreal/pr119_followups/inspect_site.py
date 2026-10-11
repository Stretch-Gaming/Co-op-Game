"""Report L_Site01 sublevel contents, threat actors and floor heights at the planned trap spots."""
import collections
import unreal as ue
editor = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
if world.get_outermost().get_name() != '/Game/Maps/L_Site01':
    assert editor.load_level('/Game/Maps/L_Site01')
    world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
by_level = collections.defaultdict(collections.Counter)
threats = []
for a in actors.get_all_level_actors():
    lvl = a.get_level().get_outermost().get_name().rsplit('/', 1)[-1]
    cls = a.get_class().get_name()
    by_level[lvl][cls] += 1
    if any(k in cls for k in ('Trap', 'Fall', 'Ghost', 'Checkpoint', 'RoundDirector')) or a.actor_has_tag('AdventureThreatSetup'):
        l = a.get_actor_location()
        threats.append({'level': lvl, 'label': a.get_actor_label(), 'class': cls, 'loc': [round(l.x), round(l.y), round(l.z)], 'tags': [str(t) for t in a.tags]})
spots = ARGS.get('spots', [])
floors = []
for x, y in spots:
    hit = ue.SystemLibrary.line_trace_single(world, ue.Vector(x, y, 1500), ue.Vector(x, y, -3000), ue.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], ue.DrawDebugTrace.NONE, True)
    if hit:
        t = hit.to_tuple()
        floors.append({'spot': [x, y], 'blocking': t[0], 'z': round(t[4].z) if t[0] else None, 'actor': t[9].get_actor_label() if t[0] and t[9] else None})
    else:
        floors.append({'spot': [x, y], 'hit': None})
RESULT = {'levels': {k: dict(v.most_common(12)) for k, v in by_level.items()}, 'threats': threats, 'floors': floors}
