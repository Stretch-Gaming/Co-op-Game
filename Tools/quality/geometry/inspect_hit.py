"""One known floor ray plus HitResult reflection inspection; no editor mutations."""
import json,pathlib
import unreal as ue
root=pathlib.Path('C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game').resolve()
assert pathlib.Path(ue.Paths.convert_relative_path_to_full(ue.Paths.get_project_file_path())).resolve()==root/'CoopGame.uproject'
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_outermost().get_name()=='/Game/Maps/L_ConnectedRoomMaze'
hit=ue.SystemLibrary.line_trace_single_by_profile(world,ue.Vector(-175,9250,-100),ue.Vector(-175,9250,-600),'Pawn',True,[],ue.DrawDebugTrace.NONE,True)
report={'type':str(type(hit)),'is_none':hit is None,'has_get_actor':hasattr(hit,'get_actor'),'has_get_component':hasattr(hit,'get_component'),'fields':{},'packages_saved':False,'queries':1}
if hit is not None:
 report['export_text']=hit.export_text()
 for name in ('blocking_hit','start_penetrating','distance','location','impact_point','impact_normal','component','actor','hit_object_handle'):
  try:
   value=hit.get_editor_property(name)
   if hasattr(value,'x')and hasattr(value,'y')and hasattr(value,'z'):value=[value.x,value.y,value.z]
   elif hasattr(value,'get_path_name'):value=value.get_path_name()
   elif value is not None and not isinstance(value,(bool,int,float,str)):value=str(value)
   report['fields'][name]={'value':value,'available':True}
  except Exception as e:report['fields'][name]={'available':False,'error':str(e)}
 if hasattr(hit,'get_actor'):
  try:
   actor=hit.get_actor();report['get_actor']=actor.get_path_name()if actor else None
  except Exception as e:report['get_actor_error']=str(e)
(root/'Saved/QualityGeometry/hit-reflection.json').write_text(json.dumps(report,indent=2));RESULT=report
