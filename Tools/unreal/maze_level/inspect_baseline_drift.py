import json,sys,difflib,hashlib
sys.path.insert(0,str(HERE))
from context import *
b=json.loads((QUEUE/'baseline.json').read_text());report={}
for path,old in b['graphs'].items():
    now={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(ue.load_asset(path))}
    changed={n:list(difflib.unified_diff(old[n].splitlines(),now.get(n,'').splitlines(),n+' before',n+' now')) for n in old if now.get(n)!=old[n]}
    report[path]=changed
(QUEUE/'baseline-dsl-drift.json').write_text(json.dumps(report,indent=2))
RESULT={p:list(changes) for p,changes in report.items() if changes}
