"""Root continuation over the exact four existing unsaved v2 nodes.

Restore only four baseline Target fan-out edges lost during native autowiring.
No node creation/deletion, baseline refresh, exec/default/position change.
"""
import ast,hashlib,json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
OUT=Path('/tmp/coop-mining');ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
PATH='/Game/Core/BP_CoopCharacter';DISK='Content/Core/BP_CoopCharacter.uasset'
state={'stage':'preflight','saved':[],'restored_edges':[]}
def receipt(): (OUT/'use-allowed-continue-partial.json').write_text(json.dumps(state,indent=2))
# Reuse only the exact snapshot/identity helpers; never run the mutation module.
tree=ast.parse((OUT/'patch_use_allowed-v2.py').read_text())
helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('snapshot','digest','pin_key','linked_keys')]
assert len(helpers)==4
exec(compile(ast.Module(body=helpers,type_ignores=[]),str(OUT/'patch_use_allowed-v2.py'),'exec'),globals())
def run():
    args=globals().get('ARGS',{});assert args.get('execute') is True
    assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
    leases=json.loads((OUT/'leases.json').read_text());locks=leases.get('locks',[]) if isinstance(leases,dict) else leases
    assert any(r['path']==DISK and r.get('owner',{}).get('name')==args['lease_owner'] for r in locks)
    baseline=json.loads((OUT/'use-allowed-inventory.json').read_text())
    partial=json.loads((OUT/'use-allowed-patch-error.json').read_text())
    assert len(partial['created'])==4 and partial['saved']==[] and partial['stage']=='compile and prove preservation'
    assert hashlib.sha256((ROOT/DISK).read_bytes()).hexdigest()==baseline['character_disk_sha256']
    protected=json.loads((OUT/'core-packet.json').read_text())['protected_sha256']
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    bp=ue.load_asset(PATH);graph=BP.get_graph(bp,'UseAllowed')
    current=json.loads((OUT/'use-allowed-current-snapshot.json').read_text());assert snapshot(graph)==current,'Unknown in-memory state; inspect again'
    nodes={n.get_name():n for n in BP.find_nodes(graph)}
    assert {n['path'] for n in current}=={n['path'] for n in baseline['graphs']['UseAllowed']['nodes']}|set(partial['created'])
    created=set(partial['created']);entry=nodes['K2Node_FunctionEntry_0'];target=entry.find_output_pin('Target')
    old_or=nodes['K2Node_CommutativeAssociativeBinaryOperator_5'];result=nodes['K2Node_FunctionResult_0']
    equality=nodes['K2Node_PromotableOperator_4'];new_or=nodes['K2Node_CommutativeAssociativeBinaryOperator_6']
    assert set(partial['created'])=={nodes[n].get_path_name() for n in ('K2Node_CallFunction_34','K2Node_VariableGet_4','K2Node_PromotableOperator_4','K2Node_CommutativeAssociativeBinaryOperator_6')}
    before=baseline['graphs']['UseAllowed']['nodes']
    repairs=[('K2Node_CallFunction_20','OtherActor'),('K2Node_CallFunction_23','self'),('K2Node_CallFunction_3','OtherActor'),('K2Node_CallFunction_6','self')]
    def normalized(rows,restore_missing=False):
        out=[]
        for node in rows:
            if node['path'] in created:continue
            node=json.loads(json.dumps(node))
            for key in ('input_pins','output_pins'):
                for pin in node[key]:
                    added=[p for p in pin['links'] if p['node'] in created]
                    if added:
                        expected={(entry.get_path_name(),'output_pins','Target'):equality.get_path_name(),
                            (old_or.get_path_name(),'output_pins','ReturnValue'):new_or.get_path_name(),
                            (result.get_path_name(),'input_pins','Allowed'):new_or.get_path_name()}
                        assert len(added)==1 and expected.get((node['path'],key,pin['name']))==added[0]['node']
                    pin['links']=[p for p in pin['links'] if p['node'] not in created]
            old=next(p for p in before if p['path']==node['path'])
            if node['path']==old_or.get_path_name():
                next(p for p in node['output_pins'] if p['name']=='ReturnValue')['links']=next(p['links'] for p in old['output_pins'] if p['name']=='ReturnValue')
            if node['path']==result.get_path_name():
                next(p for p in node['input_pins'] if p['name']=='Allowed')['links']=next(p['links'] for p in old['input_pins'] if p['name']=='Allowed')
            if restore_missing:
                for name,pin_name in repairs:
                    if node['path']==nodes[name].get_path_name():
                        pin=next(p for p in node['input_pins'] if p['name']==pin_name);assert pin['links']==[]
                        pin['links']=next(p['links'] for p in old['input_pins'] if p['name']==pin_name)
                if node['path']==entry.get_path_name():
                    next(p for p in node['output_pins'] if p['name']=='Target')['links']=next(p['links'] for p in old['output_pins'] if p['name']=='Target')
            out.append(node)
        return out
    # Exactly the four missing baseline edges, no other tolerated difference.
    assert normalized(current,restore_missing=True)==before
    for name,pin_name in repairs:
        pin=nodes[name].find_input_pin(pin_name);assert linked_keys(pin)==[]
        baseline_node=next(n for n in before if n['path']==nodes[name].get_path_name())
        old=next(p for p in baseline_node['input_pins'] if p['name']==pin_name)
        assert len(old['links'])==1 and old['links'][0]['node']==entry.get_path_name() and old['links'][0]['index']==1
    state['stage']='restore four exact original Target edges';receipt()
    for name,pin_name in repairs:
        pin=nodes[name].find_input_pin(pin_name);assert target.try_create_connection(pin),(name,pin_name)
        state['restored_edges'].append({'from':pin_key(target),'to':pin_key(pin)});receipt()
    assert normalized(snapshot(graph))==before,'Original topology not restored before compilation'
    state['stage']='compile and full preservation proof';receipt()
    BP.compile_blueprint(bp,warnings_as_errors=True)
    assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
    assert normalized(snapshot(graph))==before,'Compile changed original topology; do not save'
    assert list(BP.list_variables(bp))==partial['variables']
    graphs={g.get_name():g for g in BP.list_graphs(bp)};assert set(graphs)==set(baseline['all_graph_topology_sha256'])
    assert all(digest(g)==baseline['all_graph_topology_sha256'][name] for name,g in graphs.items() if name!='UseAllowed')
    assert linked_keys(result.find_input_pin('Allowed'))==[pin_key(new_or.find_output_pin('ReturnValue'))]
    assert linked_keys(new_or.find_input_pin('A'))==[pin_key(old_or.find_output_pin('ReturnValue'))]
    assert linked_keys(new_or.find_input_pin('B'))==[pin_key(equality.find_output_pin('ReturnValue'))]
    assert linked_keys(equality.find_input_pin('A'))==[pin_key(target)]
    for path in created:
        node=next(n for n in BP.find_nodes(graph) if n.get_path_name()==path);info=BP.get_node_infos([node])[0]
        assert all(str(p.type_id)!='Exec' for p in info.input_pins+info.output_pins)
    state.update(created=list(partial['created']),original_nodes_preserved=len(before),other_graphs_preserved=len(graphs)-1,
        new_functions=0,new_variables=0,new_exec_edges=0,after_nodes=snapshot(graph))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    state['stage']='save exact Character';receipt()
    assert ue.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False);state['saved'].append(PATH)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    state.update(stage='complete',passed=True,protected_fingerprints_preserved=True,runtime_acceptance_pending=True,
        disk_after_sha256=hashlib.sha256((ROOT/DISK).read_bytes()).hexdigest())
    (OUT/'use-allowed-patched.json').write_text(json.dumps(state,indent=2));return state
try:RESULT=run()
except Exception:
    state['error']=traceback.format_exc();receipt();(OUT/'use-allowed-continue-error.json').write_text(json.dumps(state,indent=2));raise
