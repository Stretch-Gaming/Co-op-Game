import unreal as ue
out = {}
for name in ('ATT_HZ_Trap', 'ATT_HZ_Torch', 'ATT_HZ_Drip'):
    a = ue.load_asset('/Game/Hazards/Art/Audio/' + name)
    s = a.get_editor_property('attenuation')
    out[name] = {k: str(s.get_editor_property(k)) for k in ('attenuation_shape', 'distance_algorithm', 'falloff_distance', 'attenuation_shape_extents', 'spatialize', 'attenuate', 'spatialization_algorithm', 'enable_occlusion', 'enable_listener_focus')}
for name in ('SFX_TorchCrackle_Loop', 'SFX_CaveAmbience_Loop', 'SFX_Spikes_Arm'):
    w = ue.load_asset('/Game/Hazards/Art/Audio/' + name)
    out[name] = {k: str(w.get_editor_property(k)) for k in ('looping', 'volume', 'attenuation_settings', 'sound_class_object', 'virtualization_mode', 'num_channels', 'sample_rate' if False else 'duration')}
RESULT = out
