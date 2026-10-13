"""Root-only bounded native RPC/validation readback; no compile/save/game calls."""
import json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
OUT=Path('/tmp/coop-mining')
RESULT={'inspection_only':True,'assets':{},'errors':[],'protected_packages_saved':False}
def flush():
    (OUT/'rpc-inventory-partial.json').write_text(json.dumps(RESULT,indent=2))
def pin_data(info):
    return {'name':str(info.name),'type':str(info.type_id),'value':str(info.value),
            'links':[{'node':p.node.get_path_name(),'pin_index':p.index_id,'direction':str(p.direction)} for p in info.connected_pins]}
try:
    assert Path(ue.Paths.project_dir()).resolve()==Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
    scope={
      '/Game/Core/BP_CoopCharacter':('useallowed','beginuse','validateuse','canaccept','dointeract','serverinteract','canusegameplay','canceluse'),
      '/Game/Core/BP_CoopGameMode':('canuse','gameplayallowed','inputallowed'),
      '/Game/Hazards/FirstRoom/BP_MinePickaxe':('localswing','serverswing','caninteract','updateinputbinding'),
      '/Game/Puzzles/BP_Carryable':('claim','clearcarrier','releasecarried','caninteract'),
      '/Game/Puzzles/Carrying/AC_Carrying':('trypickup','clearcarried','releasecarried','dropcarried')}
    for path,terms in scope.items():
        bp=ue.load_asset(path);assert bp
        row={'graphs':{},'rpc_event_nodes':[]};RESULT['assets'][path]=row;flush()
        graphs={g.get_name():g for g in BP.list_graphs(bp)};row['graph_names']=list(graphs)
        for name,graph in graphs.items():
            if any(t in name.lower().replace('_','') for t in terms):
                try:row['graphs'][name]=BP.read_graph_dsl(graph)
                except Exception:RESULT['errors'].append({'asset':path,'graph':name,'error':traceback.format_exc()})
                flush()
        if path=='/Game/Core/BP_CoopCharacter' and 'EventGraph' in graphs:
            for node in BP.find_nodes(graphs['EventGraph']):
                info=BP.get_node_infos([node])[0];kind=str(info.type_id).lower().replace('_','')
                if any(t in kind for t in ('serverinteractbegin','dointeractbegin','beginuse')):
                    row['rpc_event_nodes'].append({'path':node.get_path_name(),'type_id':str(info.type_id),
                      'title':str(node.get_node_title()),'input_pins':[pin_data(p) for p in info.input_pins],
                      'output_pins':[pin_data(p) for p in info.output_pins]});flush()
        flush()
    (OUT/'rpc-inventory.json').write_text(json.dumps(RESULT,indent=2))
except Exception:
    RESULT['fatal_error']=traceback.format_exc();flush()
    (OUT/'rpc-inventory-error.json').write_text(json.dumps(RESULT,indent=2));raise
