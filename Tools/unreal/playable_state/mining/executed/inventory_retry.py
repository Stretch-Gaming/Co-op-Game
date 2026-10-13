"""Root-only inspection, no mutation/save. Capture current retry hook graphs."""
import json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
OUT=Path('/tmp/coop-mining')
try:
    assert Path(ue.Paths.project_dir()).resolve()==Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
    RESULT={'inspection_only':True,'assets':{}}
    for path in ('/Game/Core/BP_CoopGameMode','/Game/Puzzles/Rounds/BP_RoundDirector','/Game/Puzzles/BP_Carryable'):
        bp=ue.load_asset(path);assert bp
        graphs={g.get_name():g for g in BP.list_graphs(bp)}
        selected=[n for n in graphs if any(t in n.lower() for t in ('retry','reset','startcarry'))]
        RESULT['assets'][path]={'graph_names':list(graphs),'graphs':{n:BP.read_graph_dsl(graphs[n]) for n in selected}}
        (OUT/'retry-inventory-partial.json').write_text(json.dumps(RESULT,indent=2))
    (OUT/'retry-inventory.json').write_text(json.dumps(RESULT,indent=2))
except Exception:
    (OUT/'retry-inventory-error.json').write_text(json.dumps({'error':traceback.format_exc()},indent=2));raise
