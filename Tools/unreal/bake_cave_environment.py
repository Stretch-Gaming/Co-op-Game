"""Run inside CoopGame's Unreal Editor with GeometryScripting enabled.

Bakes the standalone prototype's exported environment into the HZ sublevel.
Never copies the prototype's GameMode, character, input or gameplay code.
"""
import json
from pathlib import Path
import unreal

ROOT = '/Game/Hazards/Art/CavePrototype'
TAG = 'CavePrototypeIntegration'

def run():
    project = Path(unreal.Paths.project_dir()).resolve()
    manifest = json.loads((project/'SourceArt/HZ/CaveIntegration/cave.json').read_text(encoding='utf-8'))
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_name() == '/Game/Maps/L_Site01'
    hz = unreal.GameplayStatics.get_streaming_level(world, 'L_Site01_HZ')
    assert hz.get_loaded_level().get_outermost().get_name() == '/Game/Hazards/L_Site01_HZ'
    unreal.EditorLevelUtils.make_level_current(hz)
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    saved = []
    materials = {}
    parent = unreal.load_asset('/Game/Shared/Style/M_Stylized')
    assert parent

    def material(color):
        key = tuple(round(c, 4) for c in color)
        if key not in materials:
            name = 'MI_Cave_' + '_'.join(f'{round(c*255):03}' for c in color[:3])
            path = ROOT+'/Materials/'+name
            mi = unreal.load_asset(path) or assets.create_asset(name, ROOT+'/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, 'Tint', unreal.LinearColor(*color))
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, 'GradientStrength', 0.22)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, 'EdgeStrength', 0.18)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, 'RimStrength', 0.04)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, 'MetallicMultiplier', 0.0)
            unreal.MaterialEditingLibrary.update_material_instance(mi)
            saved.append(mi)
            materials[key] = mi
        return materials[key]

    glow_path = ROOT+'/Materials/M_CaveVertexGlow'
    glow = unreal.load_asset(glow_path)
    if not glow:
        glow = assets.create_asset('M_CaveVertexGlow', ROOT+'/Materials', unreal.Material, unreal.MaterialFactoryNew())
    glow.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(glow)
    vertex = unreal.MaterialEditingLibrary.create_material_expression(glow, unreal.MaterialExpressionVertexColor, -200, 0)
    assert unreal.MaterialEditingLibrary.connect_material_property(vertex, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(glow)
    saved.append(glow)

    # Only replace the original bootstrap environment and our previous bake.
    existing = list(actors.get_all_level_actors())
    for actor in existing:
        package = actor.get_level().get_outermost().get_name()
        if package == '/Game/Hazards/L_Site01_HZ' and (TAG in [str(t) for t in actor.tags] or actor.get_actor_label() in ('Floor','DirectionalLight','SkyAtmosphere','SkyLight','ExponentialHeightFog','VolumetricCloud','SM_SkySphere')):
            assert actors.destroy_actor(actor)

    def place(cls, name, record):
        p = record['location']
        pitch, yaw, roll = record['rotation']
        actor = actors.spawn_actor_from_class(cls, unreal.Vector(*p), unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll))
        assert actor and actor.get_level().get_outermost().get_name() == '/Game/Hazards/L_Site01_HZ'
        actor.set_actor_label('Cave_'+name)
        actor.set_editor_property('tags', [unreal.Name(TAG)])
        actor.set_folder_path('CavePrototype')
        actor.set_actor_scale3d(unreal.Vector(*record['scale']))
        return actor

    count = {'static':0, 'procedural':0, 'blocker':0, 'point':0}
    for index, record in enumerate(manifest['components']):
        kind = record['kind']
        label = f'{kind}_{index:03}'
        if kind in ('static', 'procedural', 'blocker'):
            actor = place(unreal.StaticMeshActor, label, record)
            component = actor.static_mesh_component
            component.set_mobility(unreal.ComponentMobility.STATIC)
            if kind == 'static':
                mesh = unreal.load_asset(record['mesh'])
            elif kind == 'blocker':
                mesh = unreal.load_asset('/Engine/BasicShapes/Cube')
                actor.set_actor_scale3d(unreal.Vector(*(e/50 for e in record['extent'])))
                actor.set_actor_hidden_in_game(True)
                component.set_editor_property('cast_shadow', False)
            else:
                path = ROOT+f'/Meshes/SM_Cave_{index:03}'
                mesh = unreal.load_asset(path)
                if not mesh:
                    dynamic = unreal.DynamicMesh()
                    buffers = unreal.GeometryScriptSimpleMeshBuffers()
                    buffers.vertices = [unreal.Vector(*v) for v in record['vertices']]
                    buffers.normals = [unreal.Vector(*v) for v in record['normals']]
                    buffers.uv0 = [unreal.Vector2D(*v) for v in record['uvs']]
                    buffers.vertex_colors = [unreal.LinearColor(*v) for v in record['vertex_colors']]
                    t = record['triangles']
                    buffers.triangles = [unreal.IntVector(*t[i:i+3]) for i in range(0,len(t),3)]
                    unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic, buffers)
                    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
                    options.enable_nanite = False
                    options.enable_collision = record['collision']
                    options.collision_mode = unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
                    mesh, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic, path, options)
                    assert mesh, (path, outcome)
                saved.append(mesh)
            assert mesh, record
            component.set_editor_property('static_mesh', mesh)
            if kind != 'blocker':
                component.set_material(0, glow if record.get('glow') else material(record['color']))
                component.set_editor_property('cast_shadow', record['shadow'])
            component.set_collision_profile_name('BlockAll' if record.get('collision', kind=='blocker') else 'NoCollision')
        elif kind == 'point':
            actor = place(unreal.PointLight, label, record)
            light = actor.get_component_by_class(unreal.PointLightComponent)
            light.set_mobility(unreal.ComponentMobility.MOVABLE)
            light.set_editor_property('intensity_units', unreal.LightUnits.CANDELAS)
            light.set_editor_property('intensity', record['intensity'])
            light.set_editor_property('attenuation_radius', record['radius'])
            light.set_light_color(unreal.LinearColor(*record['color']))
            light.set_editor_property('cast_shadows', record['shadow'])
        else:
            raise AssertionError(kind)
        count[kind] += 1

    neutral = {'location':[0,0,0], 'rotation':[0,0,0], 'scale':[1,1,1]}
    sun = place(unreal.DirectionalLight, 'AmbientSun', neutral)
    sun.set_actor_rotation(unreal.Rotator(pitch=-50,yaw=-40,roll=0), False)
    light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_editor_property('intensity', 10.0)
    light.set_editor_property('cast_shadows', False)
    light.set_editor_property('atmosphere_sun_light', True)
    light.set_editor_property('lighting_channels', unreal.LightingChannels(channel0=False,channel1=False,channel2=False))
    place(unreal.SkyAtmosphere, 'Atmosphere', neutral)
    sky = place(unreal.SkyLight, 'SkyFill', neutral).get_component_by_class(unreal.SkyLightComponent)
    sky.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.set_editor_property('real_time_capture', True)
    sky.set_editor_property('intensity', 0.55)
    sky.set_light_color(unreal.LinearColor(0.24,0.38,0.56,1))
    fog = place(unreal.ExponentialHeightFog, 'Haze', neutral).get_component_by_class(unreal.ExponentialHeightFogComponent)
    fog.set_editor_property('fog_density', 0.035)
    fog.set_editor_property('fog_height_falloff', 2.0)
    fog.set_editor_property('fog_inscattering_luminance', unreal.LinearColor(0.08,0.1,0.16,1))
    fog.set_editor_property('start_distance', 150.0)
    volume = place(unreal.PostProcessVolume, 'Exposure', neutral)
    volume.set_editor_property('unbound', True)
    settings = volume.get_editor_property('settings')
    settings.set_editor_property('override_auto_exposure_method', True)
    settings.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
    settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure', True)
    settings.set_editor_property('auto_exposure_apply_physical_camera_exposure', False)
    settings.set_editor_property('override_auto_exposure_bias', True)
    settings.set_editor_property('auto_exposure_bias', 0.0)
    settings.set_editor_property('override_bloom_intensity', True)
    settings.set_editor_property('bloom_intensity', 0.8)
    settings.set_editor_property('override_vignette_intensity', True)
    settings.set_editor_property('vignette_intensity', 0.25)
    volume.set_editor_property('settings', settings)
    for asset in saved:
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    # Explicit level saving persists transforms, including setters that do not mark packages dirty.
    assert unreal.EditorLoadingAndSavingUtils.save_packages([hz.get_loaded_level().get_outermost()], False)
    return {'environment_components':count,'materials':len(materials),'saved_assets':len(saved),'sublevel':'/Game/Hazards/L_Site01_HZ','player_game_mode_unchanged':True}
