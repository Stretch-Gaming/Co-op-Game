"""Re-apply the cave traps and fall volume from playable_game/place_adventure_threats.py to L_Site01_HZ only.

The adopted HZ cave map lost these placements in HC-INT2 (PR #119). Unlike the original script, this one
leaves every other sublevel alone: it only replaces actors tagged AdventureThreatSetup inside L_Site01_HZ
and saves only that package.
"""
import unreal as ue

LEVEL = '/Game/Hazards/L_Site01_HZ'
TAG = 'AdventureThreatSetup'
TRAPS = [('Spikes', (2000, 0, 0)), ('Darts', (6200, 0, 0)), ('Swing', (7200, 0, 0)), ('Spikes', (8000, 0, 0)), ('Spikes', (7000, 1200, 0)),
         ('Swing', (14000, 0, 0)), ('Swing', (15500, 0, 0)), ('Spikes', (14800, 0, 0)), ('Darts', (16000, 0, 0))]

assert not ue.EditorLevelLibrary.get_pie_worlds(True)
editor = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
if world.get_outermost().get_name() != '/Game/Maps/L_Site01':
    assert editor.load_level('/Game/Maps/L_Site01')
    world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
hz = ue.GameplayStatics.get_streaming_level(world, 'L_Site01_HZ')
assert hz and hz.get_loaded_level()
ue.EditorLevelUtils.make_level_current(hz)
removed = 0
for actor in actors.get_all_level_actors():
    if actor.actor_has_tag(TAG) and actor.get_level().get_outermost().get_name() == LEVEL:
        assert actors.destroy_actor(actor)
        removed += 1

def spawn(path, label, position):
    actor = actors.spawn_actor_from_class(ue.load_asset(path).generated_class(), ue.Vector(*position), ue.Rotator())
    assert actor and actor.get_level().get_outermost().get_name() == LEVEL, label
    actor.set_actor_label(label)
    actor.set_editor_property('tags', [ue.Name(TAG)])
    actor.set_folder_path('Adventure/Threats')
    return actor

placed = []
for i, (kind, pos) in enumerate(TRAPS):
    spawn('/Game/Hazards/Traps/BP_Trap_' + kind, 'Adventure_Trap_' + str(i), pos)
    placed.append(['BP_Trap_' + kind, pos])
fall = spawn('/Game/Hazards/Traps/BP_FallVolume', 'Adventure_CaveFall', (23000, 0, -3300))
fall.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(7000, 3000, 150))
placed.append(['BP_FallVolume', [23000, 0, -3300]])
assert ue.EditorLoadingAndSavingUtils.save_packages([hz.get_loaded_level().get_outermost()], False)
editor.set_current_level_by_name('L_Site01')
RESULT = {'removed': removed, 'placed': placed}
