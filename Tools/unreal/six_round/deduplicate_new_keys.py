"""UE5.8 moved live mappings; remove duplicate keys created by stale guard reads."""
import json,unreal as ue
results=[]
for name,actions in [('IMC_SixRound',{'IA_Sprint','IA_ThrowFlare','IA_Climb'}),('IMC_RunControls',{'IA_P2Flare','IA_P2Climb'})]:
    context=ue.load_asset('/Game/Core/Input/'+name)
    data=context.get_editor_property('default_key_mappings')
    kept=[];seen=set();removed=0
    for mapping in data.mappings:
        key=(mapping.action.get_path_name() if mapping.action else '',str(mapping.key.get_editor_property('key_name')))
        if mapping.action and mapping.action.get_name() in actions:
            assert not mapping.modifiers and not mapping.triggers,'Do not discard distinct authored mappings'
            if key in seen:removed+=1;continue
            seen.add(key)
        kept.append(mapping)
    if removed:
        data.set_editor_property('mappings',kept)
        context.set_editor_property('default_key_mappings',data)
        assert ue.EditorAssetLibrary.save_loaded_asset(context,False)
    results.append({'context':name,'live_mappings':len(kept),'removed_duplicates':removed})
RESULT=results
