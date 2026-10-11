"""Read-only Blueprint RPC and input-key prerequisites. Run before PIE."""
import json,hashlib
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(ue.Paths.project_dir()).resolve()
assert root==Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
c=ue.load_asset('/Game/Core/BP_CoopCharacter');assert c
assert c.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
graph=BP.get_graph(c,'EventGraph');assert graph
events={BP._get_node_info(node).type_id.rsplit('|',1)[-1]:node for node in BP.find_nodes(graph) if BP._get_node_info(node).type_id.startswith('AddEvent|Custom|')}
# Non-Edit UPROPERTY flags are not exposed by this Python/toolset build. Primary
# observes Slate Details, records the saved asset hash, then this audit verifies
# that evidence is still tied to the exact asset being inspected.
ui_path=root/'Saved/SixRound/rpc-ui-verification.json';assert ui_path.is_file(),str(ui_path)
ui=json.loads(ui_path.read_text());asset_file=root/'Content/Core/BP_CoopCharacter.uasset'
current_hash=hashlib.sha256(asset_file.read_bytes()).hexdigest()
assert ui['character_sha256']==current_hash,'RPC UI evidence is stale: re-observe after the latest Core character save'
rpc_report={}
for name in ('Server_ThrowFlare','Server_Climb','Server_StopClimb','Server_SetClimbForward'):
 assert name in events,name
 assert ui['events'][name]['server'] is True and ui['events'][name]['reliable'] is True,(name,'Rendered Details must show Run on Server and Reliable')
 assert events[name].find_then_pin().list_connected_pins(),(name,'RPC has no handler')
 rpc_report[name]={'server_reliable_from_fresh_rendered_ui':True,'asset_sha256':current_hash}
forward=events['Server_SetClimbForward'].find_output_pin('Forward');assert forward
info=BP._get_node_info(events['Server_SetClimbForward'])
types=[str(pin.type_id) for pin in info.output_pins if str(pin.name)=='Forward'];assert len(types)==1
assert 'float' in types[0].lower(),('Forward must be float',types)
rpc_report['Server_SetClimbForward']['Forward_type']=types[0]
paths={'IA_Sprint':'LeftShift','IA_ThrowFlare':'Q','IA_Climb':'T','IA_Headlamp':'F','IA_ToggleView':'V','IA_P2Brace':'RightShift','IA_P2Flare':'RightAlt','IA_P2Climb':'P'}
contexts=[]
for folder in ('/Game/Core/Input','/Game/Input'):
 for path in ue.EditorAssetLibrary.list_assets(folder,True,False):
  asset=ue.load_asset(path)
  if isinstance(asset,ue.InputMappingContext):contexts.append(asset)
key_report={}
for action_name,key_name in paths.items():
 action=ue.load_asset('/Game/Core/Input/'+action_name);assert action,action_name
 mapped=[{'context':context.get_path_name(),'key':str(mapping.key.get_editor_property('key_name'))} for context in contexts for mapping in context.default_key_mappings.mappings if mapping.action==action]
 assert any(entry['key']==key_name for entry in mapped),(action_name,key_name,mapped)
 key_report[action_name]={'required_key':key_name,'mappings':mapped}
pc=ue.load_asset('/Game/Core/BP_CoopPlayerController')
keyboard_dsl=BP.read_graph_dsl(BP.get_graph(pc,'RefreshSplitKeyboard'))
assert '/Game/Core/Input/IA_Sprint' in keyboard_dsl and '/Game/Core/Input/IA_Brace' not in keyboard_dsl
assert '/Game/Core/Input/IA_ThrowFlare' in keyboard_dsl and '/Game/Core/Input/IA_Climb' in keyboard_dsl
assert 'ResolveSecondaryLocalPawn' in keyboard_dsl and 'GetEnhancedInputLocalPlayerSubsystem' in keyboard_dsl
report={'passed':True,'scope':'saved graph/key prerequisites plus primary fresh rendered RPC Details evidence; no input execution or device acceptance','rpc_ui_evidence':str(ui_path),'rpc':rpc_report,'key_mappings':key_report,'secondary_keyboard_dsl_sha256':hashlib.sha256(keyboard_dsl.encode()).hexdigest(),'gui_requirements':'RunOnServer+Reliable for four new custom events and Forward float pin; rerun primary axis_ready stage after UI configuration'}
(root/'Saved/SixRound/pg-input-preflight.json').write_text(json.dumps(report,indent=2));RESULT=report
