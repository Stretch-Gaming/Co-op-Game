import json,unreal as ue,toolset_registry
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert Path(ue.Paths.project_dir()).resolve()==ROOT
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
audit=json.loads((HERE/'final-audit.json').read_text())
core_path='/Game/Core/BP_CoopPlayerController'
core=ue.load_asset(core_path)
baseline=json.loads((HERE/'baseline.json').read_text())['assets'][core_path]['graphs']
core_now={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(core)}
report={'protected_core_controller_graphs_unchanged':core_now==baseline,'owned_graphs_match_worker_audit':{},'saved_owned':[]}
if core_now!=baseline:report['core_graph_diff']={'baseline':baseline,'current':core_now}
for path,expected in audit['blueprints'].items():
 assert path=='/Game/Puzzles/BP_MapExit' or path.startswith(('/Game/Puzzles/Run/','/Game/Puzzles/UI/Results/','/Game/Puzzles/Test/HC_RunEnding/'))
 bp=ue.load_asset(path);now={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
 report['owned_graphs_match_worker_audit'][path]=now==expected['graphs']
 assert now==expected['graphs'],path
 with toolset_registry.tool_raising_exceptions():BP.compile_blueprint(bp,warnings_as_errors=True)
 assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE,path
 assert ue.EditorAssetLibrary.save_loaded_asset(bp,False),path
 report['saved_owned'].append(path)
report['remaining_dirty_content']=[p.get_path_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
(HERE/'primary-save-review.json').write_text(json.dumps(report,indent=2))
assert core_now==baseline,'Protected Core controller graph mismatch; inspect report'
