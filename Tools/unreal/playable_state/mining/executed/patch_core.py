"""Root mutation stage. Narrow source-builder monitor patch, reset entry splice,
literal objective pin edits. No source mine Blueprint edits/decompiler writeback.
ARGS execute=True, lease_owner=current own lease name.
"""
import json,sys,hashlib,traceback,importlib.util
from pathlib import Path
import unreal as ue
OUT=Path('/tmp/coop-mining');ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
state={'stage':'preflight','saved':[]}
def receipt(): (OUT/'core-patch-partial.json').write_text(json.dumps(state,indent=2))
def run():
    args=globals().get('ARGS',{});assert args.get('execute') is True
    assert Path(ue.Paths.project_dir()).resolve()==ROOT
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    packet=json.loads((OUT/'core-packet.json').read_text())
    leases=json.loads((OUT/'leases.json').read_text());rows=leases.get('locks',[]) if isinstance(leases,dict) else leases
    assert any(r['path']=='Content/Core/BP_CoopGameMode.uasset' and r.get('owner',{}).get('name')==args['lease_owner'] for r in rows)
    assert json.loads((OUT/'placement-finalized.json').read_text())['passed']
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in packet['protected_sha256'].items())
    spec=importlib.util.spec_from_file_location('coop_mining_private_authoring',ROOT/'Tools/unreal/six_round/authoring.py')
    authoring=importlib.util.module_from_spec(spec);spec.loader.exec_module(authoring)
    authoring.ROOT=ROOT;authoring.EXPECTED=ROOT;authoring.QUEUE=OUT
    scope={'/Game/Core/BP_CoopGameMode','/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD','/Game/Puzzles/Test/SixRound/BP_PuzzleConnectionDoor'}
    def owned(obj):
        authoring.guard()
        assert obj.get_path_name().split('.')[0] in scope, 'Out-of-scope Blueprint writer: '+obj.get_path_name()
    authoring.owned=owned
    BP,var,fn,write,compile_bp=authoring.BP,authoring.var,authoring.fn,authoring.write,authoring.compile_bp
    # Validate DSL before any declaration/edit. Installed authoring module
    # already imported its actual parser; use that reference.
    parser=authoring.blueprint_dsl
    for name,body in packet['bodies'].items():parser.parse(f'(fn {name} () {body})')
    gm=ue.load_asset('/Game/Core/BP_CoopGameMode');assert gm
    assets={o['asset']:ue.load_asset(o['asset']) for o in packet['objectives']};assets['/Game/Core/BP_CoopGameMode']=gm
    before={path:{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)} for path,bp in assets.items()}
    for n,dsl in packet['before'].items():assert before['/Game/Core/BP_CoopGameMode'][n]==dsl,n
    assert before['/Game/Core/BP_CoopGameMode']['RestockAfterCheckpointRetry']==packet['retry_before']
    assert 'ResetMiningForCheckpointRetry' not in before['/Game/Core/BP_CoopGameMode']
    literal_pins=[]
    for o in packet['objectives']:
        graph=BP.get_graph(assets[o['asset']],o['graph']);matches=[]
        for node in BP.find_nodes(graph):
            for pin in BP._get_node_info(node).input_pins:
                if o['old'] in str(pin.value):matches.append(pin)
        assert len(matches)==1,(o['graph'],len(matches))
        literal_pins.append((o,matches[0].pin_id,str(matches[0].value)))
    retry_graph=BP.get_graph(gm,'RestockAfterCheckpointRetry')
    entries=[n for n in BP.find_nodes(retry_graph) if n.get_class().get_name()=='K2Node_FunctionEntry']
    assert len(entries)==1
    entry=entries[0];old_targets=list(entry.find_then_pin().list_connected_pins());assert len(old_targets)==1
    state['stage']='preflight_native_graphs_and_pins_checked';receipt()
    for name in packet['new_int_variables']:var(gm,name,'int',0)
    fn(gm,'ResetMiningForCheckpointRetry')
    # Scope explicit declaring classes to newly referenced mining fields. The
    # generic title registry contains collisions such as GetActive/SetSolved.
    descriptor=BP.__dict__['create_node'];original=BP.create_node
    mining={n:ue.load_asset('/Game/Hazards/FirstRoom/BP_'+n).generated_class() for n in ('MinePuzzle','MineCart','MineDeposit','MinePickaxe','MineRock')}
    carry=ue.load_asset('/Game/Puzzles/BP_Carryable').generated_class()
    def create_node(graph,type_id,position,declaring_class=None):
        for n,cls in mining.items():
            if type_id.startswith('Class|BP'+n+'|') or type_id=='Utilities|Casting|CastToBP_'+n:declaring_class=cls
        if type_id.startswith('Class|BPCarryable|') or type_id=='Utilities|Casting|CastToBP_Carryable':declaring_class=carry
        return original(graph,type_id,position,declaring_class=declaring_class)
    BP.create_node=staticmethod(create_node)
    try:
        for name,body in packet['bodies'].items():
            write(gm,name,body);state['stage']='graph_written:'+name;receipt()
    finally:BP.create_node=descriptor
    reset_call=BP.create_node(retry_graph,'CallFunction|ResetMiningForCheckpointRetry',ue.IntPoint(250,-250),declaring_class=gm.generated_class())
    assert reset_call
    old_targets[0].break_single_pin_link(entry.find_then_pin())
    assert entry.find_then_pin().try_create_connection(reset_call.find_execute_pin())
    assert reset_call.find_then_pin().try_create_connection(old_targets[0])
    state['stage']='guarded_reset_entry_spliced';receipt()
    for o,pin_id,value in literal_pins:
        BP.set_pin_value(pin_id,value.replace(o['old'],o['new']))
    state['stage']='literal_objectives_changed';receipt()
    allowed={'/Game/Core/BP_CoopGameMode':{'SixRoundMonitor','MonitorSixResources','RefreshSixObjective','RestockAfterCheckpointRetry','ResetMiningForCheckpointRetry'},
             '/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD':{'UpdateSixHUD'},
             '/Game/Puzzles/Test/SixRound/BP_PuzzleConnectionDoor':{'GetInteractInfo'}}
    for path,bp in assets.items():
        compile_bp(bp)
        after={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
        assert set(after)==set(before[path])|({'ResetMiningForCheckpointRetry'} if bp==gm else set())
        assert all(after[n]==before[path][n] for n in before[path] if n not in allowed[path]), 'Unrelated graph changed: '+path
        for o in packet['objectives']:
            if o['asset']==path:assert o['new'] in after[o['graph']] and o['old'] not in after[o['graph']]
        assert ue.EditorAssetLibrary.save_loaded_asset(bp,False)
        state['saved'].append(path);state['stage']='saved:'+path;receipt()
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in packet['protected_sha256'].items())
    state.update(passed=True,protected_source_bytes_unchanged=True,method=packet['source_method'],gameplay_acceptance_pending=True)
    (OUT/'core-patched.json').write_text(json.dumps(state,indent=2))
    return state
try:RESULT=run()
except Exception:
    state.update(passed=False,error=traceback.format_exc());(OUT/'core-patch-error.json').write_text(json.dumps(state,indent=2));raise
