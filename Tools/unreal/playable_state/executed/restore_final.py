import gc,json,types
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');D=Path('/tmp/coop-runtime')
assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
record=json.loads((D/'original-play-preferences.json').read_text())
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings');perf=ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
OBJ.set_properties(settings,json.dumps(record['play']));OBJ.set_properties(perf,json.dumps(record['performance']))
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ue.SystemLibrary.execute_console_command(world,'r.ScreenPercentage '+str(json.loads((D/'original-screen-percentage.json').read_text())['r.ScreenPercentage']))
ue.SystemLibrary.execute_console_command(world,'r.AllowOcclusionQueries '+str(json.loads((D/'original-occlusion-queries.json').read_text())['value']))
R={'passed':True,'stopped':True,'packages_saved':[],'play':json.loads(OBJ.get_properties(settings,list(record['play']))),'performance':json.loads(OBJ.get_properties(perf,list(record['performance']))),'screen_percentage':ue.SystemLibrary.get_console_variable_float_value('r.ScreenPercentage'),'occlusion_queries':ue.SystemLibrary.get_console_variable_int_value('r.AllowOcclusionQueries'),'editor_map':world.get_path_name(),'slate_game_layer_visibility':{name:ue.SystemLibrary.get_console_variable_int_value(name) for name in ['Slate.GameLayer.ViewportSlotVisible','Slate.GameLayer.DebugCanvasVisible','Slate.GameLayer.PlayerCanvasVisible','Slate.GameLayer.AllCanvasesVisible']},'bridge_callbacks_removed':0}
# Remove only this task's external automation bridge callback, using its exact owned code identity.
for obj in gc.get_objects():
 if isinstance(obj,types.FunctionType) and obj.__name__=='tick' and Path(obj.__code__.co_filename).resolve()==(D/'native_dispatcher.py').resolve():
  handle=obj.__globals__.get('state',{}).get('handle')
  if handle is not None:ue.unregister_slate_post_tick_callback(handle);obj.__globals__['state']['handle']=None;R['bridge_callbacks_removed']+=1
assert R['play']==record['play'] and R['performance']==record['performance']
assert R['screen_percentage']==0.0 and R['occlusion_queries']==1 and R['bridge_callbacks_removed']==1
(D/'restored-final.json').write_text(json.dumps(R,indent=2))
