"""Bind the shared dispatcher once and immediately apply its current state."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import importlib,build
importlib.reload(build)
from build import *
guard()
state=unreal.load_asset('/Game/Core/S_RoundState')
gsclass=unreal.load_asset('/Game/Core/BP_CoopGameState').generated_class()
for name in ('BP_PuzzleSetup','BP_ChamberGate','BP_StartPad'):
    bp=unreal.load_asset('/Game/Puzzles/'+name)
    old=next((g for g in BP.list_graphs(bp) if g.get_name()=='BindState'),None)
    if old:
        for n in list(BP.find_nodes(old)):
            if not isinstance(n,(unreal.K2Node_FunctionEntry,unreal.K2Node_FunctionResult)):BP.delete_node(n)
    variable(bp,'BoundState','bool',False)
    variable(bp,'StateSource',gsclass)
    function(bp,'BindState')
    g=BP.add_function_graph(bp,'RoundChanged')
    if not any(p.name=='State' for n in BP.get_node_infos(BP.find_nodes(g,entry_points_only=True)) for p in n.output_pins):
        BP.add_struct_function_param(g,'State',state,True)
    write(bp,'RoundChanged','(fn RoundChanged (State) (CallFunction|Refresh) (CallFunction|ApplyVisual))')
    g=BP.get_graph(bp,'BindState')
    for n in list(BP.find_nodes(g)):
        if not isinstance(n,(unreal.K2Node_FunctionEntry,unreal.K2Node_FunctionResult)):BP.delete_node(n)
    text='''(fn BindState ()
     (if (not (Variables|Default|GetBoundState))
      (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
       (:then
        (Variables|Default|SetStateSource gs)
        (Variables|Default|SetBoundState true)
        (Default|BindEventtoOnRoundStateChanged :self gs :Delegate (EventDispatchers|CreateEvent :self self))
        (CallFunction|RoundChanged :State (Class|BPCoopGameState|GetRoundState :self gs))) (:CastFailed))))'''
    with toolset_registry.tool_raising_exceptions():
        blueprint_dsl.Transpiler(g,lambda graph,typ,pos:BP.create_node(graph,typ,pos,
         declaring_class=bp.generated_class() if typ.startswith('CallFunction|') else None),BP.connect_pins,BP._get_node_info,BP.set_pin_value,
         lambda x:BP.find_nodes(x),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(g,f)).transpile(text)
    delegates=[n for n in BP.find_nodes(g) if isinstance(n,unreal.K2Node_CreateDelegate)]
    assert len(delegates)==1
    target=next(n for n in BP.find_nodes(g) if isinstance(n,unreal.K2Node_AddDelegate))
    src=next(p.pin_id for p in BP._get_node_info(delegates[0]).output_pins if p.name=='OutputDelegate')
    dst=next(p.pin_id for p in BP._get_node_info(target).input_pins if p.name=='Delegate')
    BP.connect_pins(src,dst)
    BP.set_create_event_function(delegates[0],'RoundChanged')
    compile_bp(bp)
    reset='(CallFunction|ResetActor)'
    write(bp,'EventGraph',f'''(event EventBeginPlay (CallFunction|Initialize) (CallFunction|BindState))
     (event EventTick (DeltaSeconds) (CallFunction|BindState) (CallFunction|Refresh))
     (event ResetForRound (Index Attempt)
      (if (and (Networking|HasAuthority) (== Index (Variables|Default|GetRoundIndex))) {reset}))''')
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
report={}
for name in ACTORS:
    bp=unreal.load_asset('/Game/Puzzles/'+name)
    compile_bp(bp)
    report[name]={'compile':str(bp.get_editor_property('status')),'graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}}
(OUT/'compiled-graphs.json').write_text(json.dumps(report,indent=2))
