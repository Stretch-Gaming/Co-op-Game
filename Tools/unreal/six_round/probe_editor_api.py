import unreal as ue
RESULT={'level_utils':[name for name in dir(ue.EditorLevelUtils) if 'level' in name.lower()],
        'world':[name for name in dir(ue.World) if any(token in name.lower() for token in ('level','net_driver'))]}
context=ue.load_asset('/Game/Core/Input/IMC_Coop')
RESULT['coop_keys']=[{'action':m.action.get_name(),'key':str(m.key.get_editor_property('key_name'))} for m in context.default_key_mappings.mappings]
