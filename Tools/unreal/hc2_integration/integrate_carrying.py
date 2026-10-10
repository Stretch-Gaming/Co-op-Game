"""Core adapters for the reviewed carrying component; no carrying logic here."""
import unreal as ue,json,sys
sys.path.insert(0,str(HERE))
from build import load,fn,write,wire,compile_bp
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
c=load('BP_CoopCharacter')
ac=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying');assert ac
CLASS='/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C'
protected={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(c) if g.get_name() not in ['EventGraph','GetCarried','ReleaseCarried','HC1BeginPlay','EnsureCarrying','RequestDropCarried','DropFromServer']}
for name in ['EnsureCarrying','RequestDropCarried','DropFromServer']:fn(c,name)
BP.add_event(c,'Server_DropCarried');compile_bp(c)
write(c,'EnsureCarrying',f'''(fn EnsureCarrying ()
 (if (Networking|HasAuthority)
  (bind existing (Actor|GetComponentbyClass :ComponentClass "{CLASS}"))
  (Utilities|IsValid :InputObject existing
   (:"Is Valid")
   (:"Is Not Valid" (Game|AddComponentbyClass :Class "{CLASS}")))))''')
write(c,'HC1BeginPlay','''(fn HC1BeginPlay ()
 (CallFunction|EnsureCarrying)
 (CallFunction|SetupLocalInput)
 (if (Networking|HasAuthority)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ValidateUse" :Time 0.2 :bLooping true)))''')
write(c,'RequestDropCarried','''(fn RequestDropCarried ()
 (if (Pawn|IsLocallyControlled) (CallFunction|ServerDropCarried)))''')
write(c,'DropFromServer',f'''(fn DropFromServer ()
 (if (Networking|HasAuthority)
  (bind component (Utilities|Casting|CastToAC_Carrying :Object (Actor|GetComponentbyClass :ComponentClass "{CLASS}"))
   (:then (Class|ACCarrying|DropCarried :self component)) (:CastFailed))))''')
for name in ['GetCarried','ReleaseCarried']:
 write(c,name,f'''(fn {name} ()
  (if (Networking|HasAuthority)
   (bind component (Utilities|Casting|CastToAC_Carrying :Object (Actor|GetComponentbyClass :ComponentClass "{CLASS}"))
    (:then (bind item (Class|ACCarrying|{name} :self component)) (return item)) (:CastFailed (return "None")))
   (else (return "None"))))''')
wire(c,'Server_DropCarried','DropFromServer')
g=BP.get_graph(c,'EventGraph')
events=[n for n in BP.find_nodes(g) if BP._get_node_info(n).type_id=='AddEvent|EnhancedInputActionIA_Drop']
assert len(events)<=1
if not events:events=[BP.create_node(g,'Input|EnhancedActionEvents|IA_Drop',ue.IntPoint(0,2600))]
e=events[0]
if not e.find_output_pin('Started').list_connected_pins():
 call=BP.create_node(g,'CallFunction|RequestDropCarried',ue.IntPoint(400,2600));assert e.find_output_pin('Started').try_create_connection(call.find_execute_pin())
compile_bp(c)
assert {g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(c) if g.get_name() in protected}==protected,'Unrelated character graph changed'
assert ue.EditorAssetLibrary.save_loaded_asset(c)
(HERE/'carrying-integration.json').write_text(json.dumps({'passed':True,'component':'AC_Carrying','attachment':'server BeginPlay adds the reviewed replicated component only when absent; existing fixture component is reused','protected_graphs':list(protected),'server_rpc_flag':'requires editor UI configuration before acceptance','signatures_preserved':['GetCarried -> CarriedActor','ReleaseCarried -> CarriedActor']},indent=2))
ue.get_editor_subsystem(ue.AssetEditorSubsystem).open_editor_for_assets([c])


