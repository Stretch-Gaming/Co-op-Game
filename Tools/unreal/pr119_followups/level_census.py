"""Count actors per sublevel of the open map by first tag (or class when untagged)."""
import collections
import unreal as ue
out = collections.defaultdict(collections.Counter)
for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
    tag = str(a.tags[0]) if a.tags else a.get_class().get_name()
    out[a.get_level().get_outermost().get_name().rsplit('/', 1)[-1]][tag] += 1
RESULT = {k: dict(v) for k, v in out.items()}
