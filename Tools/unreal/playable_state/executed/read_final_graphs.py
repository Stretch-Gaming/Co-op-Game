"""Stopped-editor readback: serialized graph topology after final compile/save."""
import ast,hashlib,json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');OUT=Path('/tmp/coop-runtime/final-graph-proof.json')
R={'passed':False,'read_only':True,'packages_saved':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def helpers(path,names):
 tree=ast.parse(path.read_text());defs=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(defs)==len(names)
 ns={'ue':ue,'BP':BP,'hashlib':hashlib,'json':json}
 exec(compile(ast.Module(body=defs,type_ignores=[]),str(path),'exec'),ns);return ns
try:
 assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
 paths=['Content/Core/BP_CoopCharacter.uasset','Content/Core/BP_CoopGameMode.uasset','Content/Player/Ghosts/BP_Ghost.uasset','Content/Puzzles/BP_CrystalLock.uasset','Content/Puzzles/Test/SixRound/BP_PuzzleConnectionDoor.uasset','Content/Puzzles/UI/HCA3/WBP_HCA3RoundHUD.uasset']
 before={p:sha(ROOT/p) for p in paths}
 ns=helpers(Path('/tmp/coop-audit/patch_ghost_backoff.py'),{'pin_key','graph_snapshot'})
 ghost=ue.load_asset('/Game/Player/Ghosts/BP_Ghost');current=ns['graph_snapshot'](ghost)
 historical=json.loads(Path('/tmp/coop-audit/ghost-backoff-patch-report.json').read_text())['after']
 assert current==historical,'Ghost graph differs from native tested patch'
 R['ghost']={'all_graphs_match_native_patch':True,'graph_count':len(current),'historical_saved_sha256':json.loads((ROOT/'Tools/unreal/playable_state/ghosts/evidence/summary.json').read_text())['saved_ghost']['sha256'],'final_sha256':before[paths[2]]}
 ns=helpers(Path('/tmp/coop-mining/patch_use_allowed-v2.py'),{'snapshot','digest'})
 character=ue.load_asset('/Game/Core/BP_CoopCharacter');graphs={g.get_name():g for g in BP.list_graphs(character)}
 historical=json.loads(Path('/tmp/coop-mining/use-allowed-patched.json').read_text());baseline=json.loads(Path('/tmp/coop-mining/use-allowed-inventory.json').read_text())
 assert ns['snapshot'](graphs['UseAllowed'])==historical['after_nodes'],'UseAllowed differs from preserved final splice'
 assert set(graphs)==set(baseline['all_graph_topology_sha256'])
 assert all(ns['digest'](g)==baseline['all_graph_topology_sha256'][name] for name,g in graphs.items() if name!='UseAllowed')
 R['character']={'use_allowed_matches_native_patch':True,'other_graph_count':len(graphs)-1,'other_graphs_match_original':True,'historical_saved_sha256':historical['disk_after_sha256'],'final_sha256':before[paths[0]]}
 protected=json.loads(Path('/tmp/coop-mining/core-packet.json').read_text())['protected_sha256']
 cart=json.loads(Path('/tmp/coop-mining/cart-removal.json').read_text())
 cave='Content/Puzzles/Test/SixRound/L_CaveEnvironment_Test.umap'
 protected[cave]=cart['map_after_sha256']
 assert all(sha(ROOT/p)==h for p,h in protected.items()),'Protected package changed'
 assert before=={p:sha(ROOT/p) for p in paths},'Readback changed saved package bytes'
 R.update(passed=True,final_asset_sha256=before,protected_package_count=len(protected),chronology='Historical native patch receipts preserved. Final warning-free compile/save rewrote package bytes; read-only topology proof binds final files to tested graphs.')
except Exception:R['error']=traceback.format_exc()
OUT.write_text(json.dumps(R,indent=2))
