"""External, serial editor task bridge; avoids console autocomplete during PIE."""
import json, time, traceback
from pathlib import Path
import unreal as ue
D=Path('/tmp/coop-runtime'); PROJECT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
assert Path(ue.Paths.project_dir()).resolve()==PROJECT
state={'last_id':None}
original=ue.SystemLibrary.get_console_variable_int_value('r.AllowOcclusionQueries')
(D/'original-occlusion-queries.json').write_text(json.dumps({'value':original}))
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ue.SystemLibrary.execute_console_command(world,'r.AllowOcclusionQueries 0')
ue.SystemLibrary.execute_console_command(world,'r.ScreenPercentage 25')
def tick(delta):
 request=D/'native-request.json'
 if not request.exists(): return
 try:
  args=json.loads(request.read_text()); task_id=args['id']
  if state['last_id']==task_id:return
  state['last_id']=task_id
  path=Path(args['script']).resolve()
  assert path.is_file() and (str(path).startswith('/private/tmp/coop-') or str(path).startswith('/tmp/coop-') or path.is_relative_to(PROJECT/'Tools/unreal/playable_state'))
  receipt={'id':task_id,'script':str(path),'started':time.time(),'status':'running'}
  (D/'native-receipt.json').write_text(json.dumps(receipt))
  namespace={'__file__':str(path),'__name__':'__main__'}
  exec(compile(path.read_text(),str(path),'exec'),namespace)
  receipt.update(status='executed',finished=time.time())
 except Exception:
  receipt={'id':state['last_id'],'status':'error','error':traceback.format_exc(),'finished':time.time()}
 (D/'native-receipt.json').write_text(json.dumps(receipt,indent=2))
state['handle']=ue.register_slate_post_tick_callback(tick)
(D/'native-ready.json').write_text(json.dumps({'project':str(PROJECT),'occlusion_original':original,'occlusion_current':ue.SystemLibrary.get_console_variable_int_value('r.AllowOcclusionQueries'),'render_scale':25,'bridge':'serial external file queue; no gameplay changes'}))
