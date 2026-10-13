"""Root executes one native data-pin splice; no DSL rewrite or exec edits.

ARGS execute=True, lease_owner=current own exact Character lease owner.
Adds four pure nodes to the reachable LOS result only. Does not change any
function signature, variable, existing node/default/position, or exec edge.
"""
import hashlib,json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
OUT=Path('/tmp/coop-mining');ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
PATH='/Game/Core/BP_CoopCharacter';DISK='Content/Core/BP_CoopCharacter.uasset'
state={'stage':'preflight','created':[],'saved':[]}
def receipt(): (OUT/'use-allowed-patch-partial.json').write_text(json.dumps(state,indent=2))
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
def digest(graph):return hashlib.sha256(json.dumps(snapshot(graph),sort_keys=True).encode()).hexdigest()
def pin_key(pin):
    id_=BP._pin_to_id(pin)
    return (id_.node.get_path_name(),str(id_.direction),int(id_.index_id))
def linked_keys(pin):return sorted(pin_key(p) for p in pin.list_connected_pins())
def run():
    args=globals().get('ARGS',{});assert args.get('execute') is True
    assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
    leases=json.loads((OUT/'leases.json').read_text());locks=leases.get('locks',[]) if isinstance(leases,dict) else leases
    assert any(r['path']==DISK and r.get('owner',{}).get('name')==args['lease_owner'] for r in locks),'Exact own Character lock required'
    baseline=json.loads((OUT/'use-allowed-inventory.json').read_text())
    catalog=json.loads((OUT/'use-allowed-operator.json').read_text())
    assert 'Utilities|Operators|Equal(==)' in catalog['equal_actor_context']
    assert 'Math|Boolean|ORBoolean' in baseline['catalog']['ORBoolean']
    assert 'Class|ACCarrying|GetCarriedItem' in baseline['catalog']['GetCarriedItem']
    assert hashlib.sha256((ROOT/DISK).read_bytes()).hexdigest()==baseline['character_disk_sha256'],'Character disk baseline changed'
    protected=json.loads((OUT/'core-packet.json').read_text())['protected_sha256']
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    bp=ue.load_asset(PATH);assert bp
    graphs={g.get_name():g for g in BP.list_graphs(bp)};graph=graphs['UseAllowed']
    variables=list(BP.list_variables(bp))
    assert set(graphs)==set(baseline['all_graph_topology_sha256'])
    assert all(digest(g)==baseline['all_graph_topology_sha256'][name] for name,g in graphs.items()),'Native graph baseline changed'
    before=baseline['graphs']['UseAllowed']['nodes'];assert snapshot(graph)==before
    nodes={n.get_name():n for n in BP.find_nodes(graph)}
    entry=nodes['K2Node_FunctionEntry_0'];target=entry.find_output_pin('Target')
    result=nodes['K2Node_FunctionResult_0'];allowed=result.find_input_pin('Allowed')
    old_or=nodes['K2Node_CommutativeAssociativeBinaryOperator_5'];old_value=old_or.find_output_pin('ReturnValue')
    assert linked_keys(allowed)==[pin_key(old_value)],('Original LOS return edge',linked_keys(allowed),pin_key(old_value))
    # Prove the chosen result is the live entry chain. The duplicated old chain
    # has no exec into MacroInstance_1 and its Return_1 remains untouched.
    assert [p.get_owning_node().get_name() for p in entry.find_then_pin().list_connected_pins()]==['K2Node_MacroInstance_2']
    assert [p.get_owning_node().get_name() for p in result.find_execute_pin().list_connected_pins()]==['K2Node_CallFunction_24']
    assert not nodes['K2Node_MacroInstance_1'].find_input_pin('exec').list_connected_pins()
    state.update(original_node_count=len(before),graph_count=len(graphs),variables=variables,lease_owner=args['lease_owner']);receipt()
    def create(kind,pos,declaring=None):
        n=BP.create_node(graph,kind,ue.IntPoint(*pos),declaring_class=declaring)
        state['created'].append(n.get_path_name());receipt();return n
    carry=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
    state['stage']='create four pure nodes';receipt()
    component=create('Actor|GetComponentbyClass',(2400,-650))
    BP.set_pin_value(BP._pin_to_id(component.find_input_pin('ComponentClass')),'/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C')
    getter=create('Class|ACCarrying|GetCarriedItem',(2900,-650),carry)
    editor=ue.BlueprintGraphEditor.get_graph_editor(graph)
    equality=editor.create_node_from_name('Utilities|Operators|Equal(==)',ue.Vector2D(3300,-500),[target],None)
    assert isinstance(equality,ue.EdGraphNode),'Contextual Actor equality node unavailable'
    equality.set_node_pos(ue.IntPoint(3300,-500));state['created'].append(equality.get_path_name());receipt()
    new_or=create('Math|Boolean|ORBoolean',(3650,352))
    def connect(output,input_):
        if pin_key(output) in linked_keys(input_):return
        assert output.try_create_connection(input_),(output.get_pin_name(),input_.get_pin_name())
    connect(component.find_output_pin('ReturnValue'),getter.find_input_pin('self'))
    connect(getter.find_output_pin('CarriedItem'),equality.find_input_pin('B'))
    connect(equality.find_output_pin('ReturnValue'),new_or.find_input_pin('B'))
    # Target fan-out is the only new link on that original entry data pin.
    connect(target,equality.find_input_pin('A'))
    for n in (component,getter,equality,new_or):
        info=BP.get_node_infos([n])[0]
        assert all(str(p.type_id)!='Exec' for p in info.input_pins+info.output_pins),'New nodes must be pure'
    state['stage']='splice final Boolean edge';receipt()
    old_value.break_single_pin_link(allowed)
    connect(old_value,new_or.find_input_pin('A'));connect(new_or.find_output_pin('ReturnValue'),allowed)
    state['stage']='compile and prove preservation';receipt()
    BP.compile_blueprint(bp,warnings_as_errors=True)
    assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
    assert list(BP.list_variables(bp))==variables
    after_graphs={g.get_name():g for g in BP.list_graphs(bp)};assert set(after_graphs)==set(graphs)
    assert all(digest(g)==baseline['all_graph_topology_sha256'][name] for name,g in after_graphs.items() if name!='UseAllowed'),'Another graph changed'
    after=snapshot(graph);old_paths={n['path'] for n in before};created_paths=set(state['created'])
    assert {n['path'] for n in after}==old_paths|created_paths and len(created_paths)==4
    # Remove only newly added links and restore the one replaced original edge,
    # then compare every original node/default/position/data+exec pin byte-for-byte.
    normalized=[]
    for node in after:
        if node['path'] not in old_paths:continue
        node=json.loads(json.dumps(node))
        original=next(n for n in before if n['path']==node['path'])
        for key in ('input_pins','output_pins'):
            for pin in node[key]:
                added=[p for p in pin['links'] if p['node'] in created_paths]
                if added:
                    expected={
                      (entry.get_path_name(),'output_pins','Target'):equality.get_path_name(),
                      (old_or.get_path_name(),'output_pins','ReturnValue'):new_or.get_path_name(),
                      (result.get_path_name(),'input_pins','Allowed'):new_or.get_path_name()}
                    assert len(added)==1 and expected.get((node['path'],key,pin['name']))==added[0]['node'],'Unexpected link to new node'
                pin['links']=[p for p in pin['links'] if p['node'] not in created_paths]
        if node['path']==result.get_path_name():
            pin=next(p for p in node['input_pins'] if p['name']=='Allowed')
            pin['links']=next(p['links'] for n in before if n['path']==node['path'] for p in n['input_pins'] if p['name']=='Allowed')
        if node['path']==old_or.get_path_name():
            pin=next(p for p in node['output_pins'] if p['name']=='ReturnValue')
            pin['links']=next(p['links'] for n in before if n['path']==node['path'] for p in n['output_pins'] if p['name']=='ReturnValue')
        normalized.append(node)
    assert normalized==before,'An original node/default/link/position changed beyond planned edge'
    assert linked_keys(allowed)==[pin_key(new_or.find_output_pin('ReturnValue'))]
    assert linked_keys(new_or.find_input_pin('A'))==[pin_key(old_value)]
    assert linked_keys(new_or.find_input_pin('B'))==[pin_key(equality.find_output_pin('ReturnValue'))]
    state.update(original_nodes_preserved=True,other_graphs_preserved=len(graphs)-1,
                 new_functions=0,new_variables=0,new_exec_edges=0,after_nodes=after)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    state['stage']='save exact Character package';receipt()
    assert ue.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
    state['saved'].append(PATH)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    state.update(passed=True,stage='complete',protected_fingerprints_preserved=True,
        disk_after_sha256=hashlib.sha256((ROOT/DISK).read_bytes()).hexdigest(),runtime_acceptance_pending=True)
    (OUT/'use-allowed-patched.json').write_text(json.dumps(state,indent=2));return state
try:RESULT=run()
except Exception:
    state['error']=traceback.format_exc();receipt();(OUT/'use-allowed-patch-error.json').write_text(json.dumps(state,indent=2));raise
