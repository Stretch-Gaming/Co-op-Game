import sys,json
sys.path.insert(0,str(HERE))
from context import *
bp=ue.load_asset('/Game/Player/Tools/BP_Flare');g=BP.get_graph(bp,'RefreshFlare')
report={q:BP.find_node_types(g,q) for q in ['IsPlaying','CreateDynamicMaterialInstance','SetScalarParameterValue','SetVolumeMultiplier','Play','Stop']}
(QUEUE/'flare-api.json').write_text(json.dumps(report,default=str,indent=2))
RESULT=report
