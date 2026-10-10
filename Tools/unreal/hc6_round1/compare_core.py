"""Read-only comparison of Core graphs; never compile or save Core."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
before=json.loads((OUT/'contracts.json').read_text())
report={'project':str(ROOT),'core_saved':False,'comparisons':{}}
for name in ('BP_CoopGameMode','BP_CoopGameState','BPI_RoundReset'):
    bp=unreal.load_asset('/Game/Core/'+name)
    after={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
    report['comparisons'][name]={'unchanged':after==before[name]}
    if after!=before[name]:report['comparisons'][name]['after']=after
report['passed']=all(v['unchanged'] for v in report['comparisons'].values())
(OUT/'core-comparison.json').write_text(json.dumps(report,indent=2))
