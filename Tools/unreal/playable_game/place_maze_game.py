import gzip, json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
editor = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level('/Game/Maps/L_Maze')
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
scene = json.loads(gzip.decompress((ROOT / 'SourceArt/HC/MazeIntegration/scene.json.gz').read_bytes()))
tag = 'AdventureMazeSetup'
for actor in actors.get_all_level_actors():
    if actor.actor_has_tag(tag):
        assert actors.destroy_actor(actor)

def current(name, path):
    level = ue.GameplayStatics.get_streaming_level(world, name)
    assert level and level.get_loaded_level().get_outermost().get_name() == path
    ue.EditorLevelUtils.make_level_current(level)
    return level.get_loaded_level().get_outermost()

def spawn(cls, label, location, yaw=0):
    actor = actors.spawn_actor_from_class(cls, ue.Vector(*location), ue.Rotator(yaw=yaw))
    assert actor
    actor.set_actor_label(label)
    actor.set_editor_property('tags', [ue.Name(tag)])
    return actor
hz = current('L_Maze_HZ', '/Game/Hazards/L_Maze_HZ')
sun = spawn(ue.DirectionalLight, 'Maze_AtmosphereSun', (0, 0, 1000))
sun.set_actor_rotation(ue.Rotator(pitch=-50, yaw=-40), False)
light = sun.get_component_by_class(ue.DirectionalLightComponent)
light.set_mobility(ue.ComponentMobility.MOVABLE)
light.set_editor_property('intensity', 10)
light.set_editor_property('cast_shadows', False)
light.set_editor_property('atmosphere_sun_light', True)
light.set_editor_property('lighting_channels', ue.LightingChannels(channel0=False, channel1=False, channel2=False))
spawn(ue.SkyAtmosphere, 'Maze_Atmosphere', (0, 0, 0))
sky = spawn(ue.SkyLight, 'Maze_SkyFill', (0, 0, 500)).get_component_by_class(ue.SkyLightComponent)
sky.set_mobility(ue.ComponentMobility.MOVABLE)
sky.set_editor_property('real_time_capture', True)
sky.set_editor_property('intensity', 0.55)
sky.set_light_color(ue.LinearColor(0.55, 0.85, 1, 1))
fog = spawn(ue.ExponentialHeightFog, 'Maze_Haze', (0, 0, 0)).get_component_by_class(ue.ExponentialHeightFogComponent)
fog.set_editor_property('fog_density', 0.025)
fog.set_editor_property('fog_height_falloff', 2)
fog.set_editor_property('fog_inscattering_luminance', ue.LinearColor(0.025, 0.06, 0.075, 1))
fog.set_editor_property('start_distance', 150)
volume = spawn(ue.PostProcessVolume, 'Maze_Exposure', (0, 0, 0))
volume.set_editor_property('unbound', True)
s = volume.settings
for name, value in [('override_auto_exposure_method', True), ('auto_exposure_method', ue.AutoExposureMethod.AEM_MANUAL), ('override_auto_exposure_apply_physical_camera_exposure', True), ('auto_exposure_apply_physical_camera_exposure', False), ('override_auto_exposure_bias', True), ('auto_exposure_bias', 0.0), ('override_bloom_intensity', True), ('bloom_intensity', 0.8), ('override_vignette_intensity', True), ('vignette_intensity', 0.25)]:
    s.set_editor_property(name, value)
volume.set_editor_property('settings', s)
sound = spawn(ue.AmbientSound, 'Maze_Ambience', (0, 9250, -250))
sound.audio_component.set_sound(ue.load_asset('/Game/Hazards/Art/Audio/SFX_CaveAmbience_Loop'))
sound.audio_component.set_editor_property('auto_activate', True)
sound.audio_component.set_editor_property('volume_multiplier', 0.4)
assert ue.EditorLoadingAndSavingUtils.save_packages([hz], False)
hc = current('L_Maze_HC', '/Game/Puzzles/L_Maze_HC')
for index, record in enumerate(scene['movers']):
    actor = spawn(ue.load_asset('/Game/Puzzles/Maze/BP_MazeMover').generated_class(), 'Maze_CoopMover_' + str(index), record['rest'], record['rotation'][1])
    actor.set_actor_scale3d(ue.Vector(*record['scale']))
    actor.set_editor_property('Rest', ue.Vector(*record['rest']))
    actor.set_editor_property('Active', ue.Vector(*record['active']))
    actor.set_editor_property('NeedsBrace', record['needs_brace'])
    actor.set_editor_property('MoveSpeed', 450 if record['gate'] else 150)
    for plate, p in enumerate(record['plates']):
        actor.set_editor_property('Plate' + str(plate + 1) + 'Center', ue.Vector(*[(a + b) / 2 for a, b in zip(p['min'], p['max'])]))
        actor.set_editor_property('Plate' + str(plate + 1) + 'Extent', ue.Vector(*[(b - a) / 2 + 5 for a, b in zip(p['min'], p['max'])]))
    actor.set_editor_property('HasPlate2', len(record['plates']) > 1)
    actor.set_editor_property('HasKeepOpen', record['keep_open_valid'])
    if record['keep_open_valid']:
        actor.set_editor_property('KeepCenter', ue.Vector(*[(a + b) / 2 for a, b in zip(record['keep_open_min'], record['keep_open_max'])]))
        actor.set_editor_property('KeepExtent', ue.Vector(*[(b - a) / 2 + 10 for a, b in zip(record['keep_open_min'], record['keep_open_max'])]))
    actor.static_mesh_component.set_material(0, ue.load_asset('/Game/Puzzles/Art/MazeIntegration/Materials/MI_MazeTint_' + '_'.join((str(round(c * 10000)) for c in record['color'][:3])) + '_Flat') or ue.load_asset('/Game/Shared/Style/MI_Stylized_Wood'))
for station in scene['stations']:
    actor = spawn(ue.TextRenderActor, 'Maze_Hint_' + station['name'], [station['location'][0], station['location'][1], station['location'][2] + 200], station['yaw'] - 90)
    text = actor.text_render
    text.set_text(ue.Text(station['name'] + '\n' + station['description']))
    text.set_world_size(20)
    text.set_text_render_color(ue.Color(238, 217, 159, 255))
    text.set_horizontal_alignment(ue.HorizTextAligment.EHTA_CENTER)
spawn(ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator').generated_class(), 'Maze_RunCoordinator', (0, 0, 0))
exit = spawn(ue.load_asset('/Game/Puzzles/BP_MapExit').generated_class(), 'Maze_Exit', (0, 23200, 750))
exit.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(550, 500, 250))
for index, position in enumerate([(480, 280, 70), (620, -620, 70), (300, 9250, -230), (-350, 15500, 470), (0, 22500, 670)]):
    spawn(ue.load_asset('/Game/Puzzles/BP_Relic').generated_class(), 'Maze_Relic_' + str(index), position)
assert ue.EditorLoadingAndSavingUtils.save_packages([hc], False)
RESULT = {'stations': len(scene['stations']), 'movers': len(scene['movers']), 'relics': 5, 'exit': True, 'editor_only_authored': True, 'runtime_acceptance_pending': True}
(QUEUE / 'maze-setup.json').write_text(json.dumps(RESULT, indent=2))