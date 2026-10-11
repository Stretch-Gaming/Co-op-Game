"""Turn off collision on the maze's post-process grading box in L_Maze_HZ.

Prototypes/CoopCave exports every UBoxComponent as a "blocker", including MazeGradeBounds
(ACoopPlayground::BuildMazeGrade), a QueryOnly box that ignores every channel and only measures the
maze's colour-grade fade. place_maze_scene.py places blockers as hidden BlockAll cubes, so that box became
an invisible solid around the whole maze (11000 x 11625 x 2050 half-extent), and every player inside the
maze started in penetration. The cave's real blockers are walls and a lid of at most 1450 cm half-extent,
so a blocker wider than GRADE_MIN on both X and Y is the grading box.
"""
import gzip, json
import unreal as ue
GRADE_MIN = 5000
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
editor = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
scene = json.loads(gzip.decompress((ROOT / 'SourceArt/HC/MazeIntegration/scene.json.gz').read_bytes()))
grade = {'MazeScene_%d' % i: c['name'] for i, c in enumerate(scene['components']) if c['kind'] == 'blocker' and c['extent'][0] > GRADE_MIN and c['extent'][1] > GRADE_MIN}
assert len(grade) == 1, grade
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
if world.get_outermost().get_name() != '/Game/Maps/L_Maze':
    assert editor.load_level('/Game/Maps/L_Maze')
    world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
hz = ue.GameplayStatics.get_streaming_level(world, 'L_Maze_HZ').get_loaded_level().get_outermost()
fixed = []
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() in grade and actor.actor_has_tag('PlayableMazeScene'):
        assert actor.get_level().get_outermost() == hz
        component = actor.static_mesh_component
        component.set_collision_profile_name('NoCollision')
        component.set_collision_enabled(ue.CollisionEnabled.NO_COLLISION)
        actor.tags = list(actor.tags) + [ue.Name('MazeGradeBounds')]
        fixed.append(actor.get_actor_label())
assert fixed == list(grade), fixed
assert ue.EditorLoadingAndSavingUtils.save_packages([hz], False)
RESULT = {'no_collision': {k: grade[k] for k in fixed}}
