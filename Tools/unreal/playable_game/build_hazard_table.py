import sys
sys.path.insert(0,str(HERE))
from authoring import *
from editor_toolset.toolsets.object import ObjectTools
from editor_toolset.toolsets.data_table import DataTableTools
guard()
struct=ue.load_asset('/Game/Hazards/S_HazardScaling')
schema=json.loads(ObjectTools.list_properties(struct))
assert set(schema)=={'spikeDelay','dartInterval','swingSpeed','reviveSeconds'},schema
assert all(schema[name]['type']=='number' for name in schema),schema
assert ue.EditorAssetLibrary.save_loaded_asset(struct,False)
table=ue.load_asset('/Game/Hazards/DT_HazardScaling') or DataTableTools.create('/Game/Hazards','DT_HazardScaling',struct)
rows={'2':{'spikeDelay':.6,'dartInterval':3.0,'swingSpeed':.8,'reviveSeconds':3.0},'3':{'spikeDelay':.5,'dartInterval':2.5,'swingSpeed':1.0,'reviveSeconds':3.5},'4':{'spikeDelay':.4,'dartInterval':2.0,'swingSpeed':1.2,'reviveSeconds':4.0}}
existing=json.loads(DataTableTools.get_rows(table,[]))
missing=[name for name in rows if name not in existing]
if missing:
    DataTableTools.add_rows(table,missing)
DataTableTools.set_rows(table,json.dumps(rows))
assert ue.EditorAssetLibrary.save_loaded_asset(table,False)
RESULT={'schema':schema,'rows':json.loads(DataTableTools.get_rows(table,['2','3','4']))}
(QUEUE/'hazard-table.json').write_text(json.dumps(RESULT,indent=2))
