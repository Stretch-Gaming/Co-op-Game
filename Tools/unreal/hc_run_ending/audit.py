import json,unreal as ue,toolset_registry
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert Path(ue.Paths.project_dir()).resolve()==ROOT and ue.SystemLibrary.get_engine_version().startswith('5.8.3-58210709')
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
paths=['/Game/Puzzles/BP_MapExit','/Game/Puzzles/Run/BP_RunCoordinator','/Game/Puzzles/UI/Results/AC_RunResults','/Game/Puzzles/UI/Results/WBP_RunResults','/Game/Puzzles/Test/HC_RunEnding/BP_RunEndingFixtureGM','/Game/Puzzles/Test/HC_RunEnding/BP_RunEndingFixturePC']
report={'passed':True,'identity':json.loads((HERE/'editor-identity.json').read_text()),'blueprints':{},'gi_gs_native_links':{}}
for path in paths:
 bp=ue.load_asset(path);assert bp
 with toolset_registry.tool_raising_exceptions():BP.compile_blueprint(bp,warnings_as_errors=True)
 assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
 report['blueprints'][path]={'compile':'up to date; warnings_as_errors true','graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}}
co=ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator')
for name in ['CaptureSnapshot','RestoreResults','RequestRestart']:
 out=[]
 for n in BP.find_nodes(BP.get_graph(co,name)):
  info=BP._get_node_info(n)
  if 'SetRelics' not in info.type_id:continue
  entry={'node':str(n),'type_id':info.type_id,'inputs':[]}
  for pin in info.input_pins:
   entry['inputs'].append({'name':pin.name,'native_type':pin.type_id,'value':pin.value,'linked_nodes':[BP._get_node_info(p.get_owning_node()).type_id for p in BP._resolve_pin(pin.pin_id).list_connected_pins()]})
  try:entry['native_variable_reference']=str(n.get_editor_property('variable_reference'))
  except Exception:pass
  out.append(entry)
 report['gi_gs_native_links'][name]=out
(HERE/'final-audit.json').write_text(json.dumps(report,indent=2))
