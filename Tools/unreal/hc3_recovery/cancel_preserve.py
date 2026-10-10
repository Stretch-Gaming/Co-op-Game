"""Cancellation only: preserve owned packages, stop the command loop."""
import inspect,json,unreal
owned_prefixes=('/Game/Puzzles/Recovery/','/Game/Puzzles/Test/HC3/')
content=unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
maps=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
saved=[]
for package in content:
 if package.get_name().startswith(owned_prefixes):
  assert unreal.EditorLoadingAndSavingUtils.save_packages([package],True)
  saved.append(package.get_name())
remaining_content=unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
remaining_maps=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
report={'saved_owned_packages':saved,'remaining_dirty_content':[p.get_name() for p in remaining_content],'remaining_dirty_maps':[p.get_name() for p in remaining_maps],'automation_stopped':True,'editor_closed':False,'reason':'Unowned dirty package retained intact; no discard authorized.'}
(HERE/'cancelled-preservation.json').write_text(json.dumps(report,indent=2))
caller=inspect.currentframe().f_back
assert caller.f_code.co_name=='tick'
unreal.unregister_slate_post_tick_callback(caller.f_globals['handle'])
if not remaining_content and not remaining_maps:
 report['editor_closed']=True
 (HERE/'cancelled-preservation.json').write_text(json.dumps(report,indent=2))
 unreal.SystemLibrary.quit_editor()
