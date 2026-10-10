"""Repair malformed legacy key names; keep secondary arrows off the primary map."""
import json,unreal as ue
context=ue.load_asset('/Game/Core/Input/IMC_Coop')
data=context.get_editor_property('default_key_mappings')
kept=[];removed=[]
for mapping in data.mappings:
    key=str(mapping.key.get_editor_property('key_name'))
    if key=='(' or (mapping.action.get_name()=='IA_Move' and key in ('Up','Down','Left','Right')):
        removed.append({'action':mapping.action.get_name(),'key':key});continue
    kept.append(mapping)
data.set_editor_property('mappings',kept);context.set_editor_property('default_key_mappings',data)
for action_name,keys in {'IA_ToggleView':['V','Gamepad_RightThumbstick'],'IA_Interact':['E','Gamepad_FaceButton_Left'],'IA_Drop':['X','Gamepad_FaceButton_Right'],'IA_Headlamp':['F','Gamepad_LeftShoulder']}.items():
    action=ue.load_asset('/Game/Core/Input/'+action_name);assert action
    for name in keys:
        key=ue.Key();key.set_editor_property('key_name',ue.Name(name))
        if not any(m.action==action and m.key==key for m in context.default_key_mappings.mappings):context.map_key(action,key)
assert ue.EditorAssetLibrary.save_loaded_asset(context,False)
RESULT={'removed':removed,'live_keys':[{'action':m.action.get_name(),'key':str(m.key.get_editor_property('key_name'))} for m in context.default_key_mappings.mappings],'secondary_arrow_ownership':True,'physical_input_pending':True}
(QUEUE/'primary-key-repair.json').write_text(json.dumps(RESULT,indent=2))
