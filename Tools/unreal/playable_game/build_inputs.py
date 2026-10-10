import sys
import importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
assets=ue.AssetToolsHelpers.get_asset_tools()
folder='/Game/Core/Input'
definitions={'IA_Brace':['LeftShift','Gamepad_LeftTrigger'],'IA_RunRestart':['R','Gamepad_Special_Right'],'IA_AddLocalPlayer':['F5'],'IA_RemoveLocalPlayer':['F6']}
actions={}
for name,keys in definitions.items():
    action=ue.load_asset(folder+'/'+name) or assets.create_asset(name,folder,ue.InputAction,ue.InputAction_Factory())
    action.set_editor_property('value_type',ue.InputActionValueType.BOOLEAN)
    action.set_editor_property('consume_input',False)
    assert ue.EditorAssetLibrary.save_loaded_asset(action,False)
    actions[name]=action
context=ue.load_asset(folder+'/IMC_RunControls') or assets.create_asset('IMC_RunControls',folder,ue.InputMappingContext,ue.InputMappingContext_Factory())
for name,keys in definitions.items():
    for key in keys:
        typed_key=ue.Key()
        typed_key.set_editor_property('key_name',ue.Name(key))
        exists=any(m.action==actions[name] and m.key==typed_key for m in context.get_editor_property('mappings'))
        if not exists:context.map_key(actions[name],typed_key)
assert ue.EditorAssetLibrary.save_loaded_asset(context,False)
character=ue.load_asset('/Game/Core/BP_CoopCharacter')
pc=ue.load_asset('/Game/Core/BP_CoopPlayerController')
fn(pc,'SetupRunInput')
write(pc,'SetupRunInput',f'''
 (if (and (Pawn|IsLocalPlayerController) (not {V('RunInputAdded')}))
  (bind subsystem (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController self))
  (Utilities|IsValid :InputObject subsystem
   (:"Is Valid"
    (Input|AddMappingContext :self subsystem :MappingContext "/Game/Core/Input/IMC_RunControls.IMC_RunControls" :Priority 2)
    {S('RunInputAdded','true')}) (:"Is Not Valid")))''')
write(pc,'RemoveRunInput',f'''
 (if {V('RunInputAdded')}
  (bind subsystem (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController self))
  (Utilities|IsValid :InputObject subsystem
   (:"Is Valid" (Input|RemoveMappingContext :self subsystem :MappingContext "/Game/Core/Input/IMC_RunControls.IMC_RunControls") {S('RunInputAdded','false')}) (:"Is Not Valid")))''')
event(pc,'ReceiveBeginPlay','HC1SetupDebugInput')
event(pc,'ReceiveBeginPlay','SetupRunInput')
event(pc,'ReceiveEndPlay','RemoveRunInput')

def bind_action(bp,name,handlers):
    graph=BP.get_graph(bp,'EventGraph')
    matches=[n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id in ('Input|EnhancedActionEvents|'+name,'Input|EnhancedActionEvents|EnhancedInputAction'+name)]
    node=matches[0] if matches else BP.create_node(graph,'Input|EnhancedActionEvents|'+name,ue.IntPoint(100,5000))
    for output,handler in handlers.items():
        links=list(node.find_output_pin(output).list_connected_pins())
        if any(handler in BP._get_node_info(p.get_owning_node()).type_id for p in links):continue
        for target in links:node.find_output_pin(output).break_single_pin_link(target)
        call=BP.create_node(graph,'CallFunction|'+handler,ue.IntPoint(550,5000),declaring_class=bp.generated_class())
        assert node.find_output_pin(output).try_create_connection(call.find_execute_pin())

bind_action(character,'IA_Brace',{'Started':'RequestBraceStart','Completed':'RequestBraceStop','Canceled':'RequestBraceStop'})
bind_action(character,'IA_ToggleView',{'Started':'RequestViewToggle'})
bind_action(character,'IA_Headlamp',{'Started':'RequestHeadlampToggle'})
bind_action(character,'IA_Jump',{'Started':'RequestJump'})
bind_action(pc,'IA_RunRestart',{'Started':'RequestRunRestart'})
bind_action(pc,'IA_AddLocalPlayer',{'Started':'HostAddLocalPlayer'})
bind_action(pc,'IA_RemoveLocalPlayer',{'Started':'HostRemoveLocalPlayer'})
save(character)
save(pc)
RESULT={'added_context':'/Game/Core/Input/IMC_RunControls','character_actions':['brace','view','headlamp','boost-jump'],'controller_actions':['restart','add local player','remove local player'],'per_local_player':True,'runtime_acceptance_pending':True}
(QUEUE/'input-build.json').write_text(json.dumps(RESULT,indent=2))
