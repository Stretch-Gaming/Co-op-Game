"""Root read-only node/pin baseline for one UseAllowed Boolean splice."""
import hashlib,json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
OUT=Path('/tmp/coop-mining')
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
PATH='/Game/Core/BP_CoopCharacter'
RESULT={'inspection_only':True,'asset':PATH,'graphs':{},'catalog':{},'errors':[],'saved_packages':[]}
def flush(): (OUT/'use-allowed-inventory-partial.json').write_text(json.dumps(RESULT,indent=2))
def snapshot(graph):
    rows=[]
    for node in BP.find_nodes(graph):
        info=BP.get_node_infos([node])[0]
        def pins(values):
            return [{'name':str(p.name),'type':str(p.type_id),'value':str(p.value),
                'links':sorted([{'node':c.node.get_path_name(),'direction':str(c.direction),'index':c.index_id} for c in p.connected_pins],key=lambda x:(x['node'],x['direction'],x['index']))} for p in values]
        rows.append({'path':node.get_path_name(),'class':node.get_class().get_name(),'type_id':str(info.type_id),
             'position':[info.position.x,info.position.y],'input_pins':pins(info.input_pins),'output_pins':pins(info.output_pins)})
    return sorted(rows,key=lambda x:x['path'])
try:
    assert Path(ue.Paths.project_dir()).resolve()==ROOT
    assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE for this baseline readback'
    bp=ue.load_asset(PATH);assert bp
    graphs={g.get_name():g for g in BP.list_graphs(bp)}
    for name in ('UseAllowed','GetCarried'):
        RESULT['graphs'][name]={'dsl':BP.read_graph_dsl(graphs[name]),'nodes':snapshot(graphs[name])};flush()
    RESULT['all_graph_topology_sha256']={name:hashlib.sha256(json.dumps(snapshot(graph),sort_keys=True).encode()).hexdigest() for name,graph in graphs.items()}
    RESULT['character_disk_sha256']=hashlib.sha256((ROOT/'Content/Core/BP_CoopCharacter.uasset').read_bytes()).hexdigest()
    for term in ('GetCarried','GetComponentbyClass','CastToAC_Carrying','GetCarriedItem','Equal(Object)','ORBoolean'):
        try:RESULT['catalog'][term]=[str(x) for x in BP.find_node_types(graphs['UseAllowed'],term)]
        except Exception:RESULT['errors'].append({'term':term,'error':traceback.format_exc()})
        flush()
    (OUT/'use-allowed-inventory.json').write_text(json.dumps(RESULT,indent=2))
except Exception:
    RESULT['fatal_error']=traceback.format_exc();flush()
    (OUT/'use-allowed-inventory-error.json').write_text(json.dumps(RESULT,indent=2));raise
