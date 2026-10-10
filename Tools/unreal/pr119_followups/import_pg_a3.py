"""PG-A3 (#37): import the taking (PG-6, #106) and chase (PG-10, #108) sounds into /Game/Player/Art/Audio.

Follows SourceArt/PG/PG-A3/README.md: files ending in _2D play on one player's screen, so they get no
attenuation; everything else plays in 3D at the victim, the dropped headlamp or the taker. Loops loop.
Attenuation mirrors HZ-A6's sphere + Natural Sound settings. The chase build layer starts at 0.5 volume
(about -6 dB) under the drone, as the README suggests; every volume still needs a check by ear.
"""
import unreal as ue

FOLDER = '/Game/Player/Art/Audio'
SOURCE = ROOT / 'SourceArt/PG/PG-A3'
ATTENUATION = {'ATT_PG_Taking': (300.0, 3000.0), 'ATT_PG_Taker': (150.0, 1500.0)}
SOUNDS = {
    'SFX_Taking_HandDrag': ('ATT_PG_Taking', False, 1.0),
    'SFX_Taking_FloorCrack': ('ATT_PG_Taking', False, 1.0),
    'SFX_Taking_FloorShut': ('ATT_PG_Taking', False, 1.0),
    'SFX_Taking_LightsOut': ('ATT_PG_Taking', False, 1.0),
    'SFX_Taking_HeadlampRoll': ('ATT_PG_Taking', False, 1.0),
    'SFX_Taking_Sting_2D': (None, False, 1.0),
    'SFX_Taker_Breath_Loop': ('ATT_PG_Taker', True, 1.0),
    'SFX_Chase_Loop_2D': (None, True, 1.0),
    'SFX_Chase_Build_Loop_2D': (None, True, 0.5),
}

assert not ue.EditorLevelLibrary.get_pie_worlds(True)
tools = ue.AssetToolsHelpers.get_asset_tools()
attenuations = {}
for name, (inner, falloff) in ATTENUATION.items():
    path = f'{FOLDER}/{name}'
    asset = ue.load_asset(path) or tools.create_asset(name, FOLDER, ue.SoundAttenuation, ue.SoundAttenuationFactory())
    settings = asset.get_editor_property('attenuation')
    settings.set_editor_property('attenuate', True)
    settings.set_editor_property('spatialize', True)
    settings.set_editor_property('attenuation_shape', ue.AttenuationShape.SPHERE)
    settings.set_editor_property('distance_algorithm', ue.AttenuationDistanceModel.NATURAL_SOUND)
    settings.set_editor_property('attenuation_shape_extents', ue.Vector(inner, 0, 0))
    settings.set_editor_property('falloff_distance', falloff)
    asset.set_editor_property('attenuation', settings)
    assert ue.EditorAssetLibrary.save_loaded_asset(asset, False)
    attenuations[name] = asset

tasks = []
for name in SOUNDS:
    task = ue.AssetImportTask()
    task.set_editor_property('filename', str(SOURCE / f'{name}.wav'))
    task.set_editor_property('destination_path', FOLDER)
    task.set_editor_property('destination_name', name)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', False)
    tasks.append(task)
tools.import_asset_tasks(tasks)

report = {}
for name, (attenuation, looping, volume) in SOUNDS.items():
    wave = ue.load_asset(f'{FOLDER}/{name}')
    assert isinstance(wave, ue.SoundWave), name
    wave.set_editor_property('looping', looping)
    wave.set_editor_property('volume', volume)
    wave.set_editor_property('attenuation_settings', attenuations[attenuation] if attenuation else None)
    if looping:
        wave.set_editor_property('virtualization_mode', ue.VirtualizationMode.RESTART)
    assert ue.EditorAssetLibrary.save_loaded_asset(wave, False)
    report[name] = {'duration': round(wave.get_editor_property('duration'), 2), 'channels': wave.get_editor_property('num_channels'),
                    'looping': looping, 'volume': volume, 'attenuation': attenuation or '2D (none)',
                    'source': str(wave.get_editor_property('asset_import_data').get_first_filename()).split('Co-op-Game/')[-1]}
RESULT = report
