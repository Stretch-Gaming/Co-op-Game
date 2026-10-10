import json,unreal
content=unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
maps=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
report={'content':[p.get_name() for p in content],'maps':[p.get_name() for p in maps],'quit_methods':[n for n in dir(unreal.SystemLibrary) if 'quit' in n.lower()]}
(HERE/'cancelled-inventory.json').write_text(json.dumps(report,indent=2))
