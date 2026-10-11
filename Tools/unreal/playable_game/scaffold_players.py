import sys
import importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *

guard()
health = create('/Game/Hazards/AC_Health', ue.ActorComponent.static_class())
BP.get_default_object(health).set_is_replicated(True)
for n,t,val,rep in [('Health','float',100.0,True),('MaxHealth','float',100.0,True),('bDowned','bool',False,True)]:
    var(health,n,t,val,notify=rep,editable=n=='MaxHealth')
for name in ('ApplyHealthState','ResetHealth','StartHealth'):
    fn(health,name)
fn(health,'IsDowned',outputs=[('Downed','bool')])
fn(health,'GetReviveSeconds',outputs=[('Seconds','float')])
fn(health,'TakeDamage',inputs=[('Damage','float')])
fn(health,'Revive',inputs=[('Reviver',ue.Actor.static_class())])
for name in ('OnDowned','OnRevived'):
    if name not in [g.get_name() for g in BP.list_graphs(health)]:
        BP.add_event_dispatcher(health,name)
compile_bp(health)

view = create('/Game/Player/AC_PlayerView', ue.ActorComponent.static_class())
BP.get_default_object(view).set_is_replicated(True)
for n,t,val in [('ViewMode','int',0),('bHeadlampOn','bool',False)]:
    var(view,n,t,val,notify=True)
var(view,'LastColorSlot','int',-1)
for name in ('ApplyViewState','ToggleView','ToggleHeadlamp','ApplyColorSlot','StartView','RefreshView'):
    fn(view,name)
compile_bp(view)

character = ue.load_asset('/Game/Core/BP_CoopCharacter')
for n,t,val,rep in [('bBraced','bool',False,True),('UnbracedSpeed','float',500.0,False),('LastBoostTime','float',-10.0,False),('BraceInputHeld','bool',False,False)]:
    var(character,n,t,val,notify=rep)
var(character,'ReviveTarget',ue.Actor.static_class())
for name in ('AdventurePlayerBegin','AdventurePlayerEnd','AdventureControllerChanged','RefreshAdventurePlayer','ApplyBrace','BraceOnServer','UnbraceOnServer','RequestBraceStart','RequestBraceStop','RequestViewToggle','RequestHeadlampToggle','ViewToggleOnServer','HeadlampToggleOnServer','RequestBoost','BoostOnServer','RequestJump','CreateReviveTarget'):
    fn(character,name)
fn(character,'ReceiveHealthDamage',inputs=[('Damage','float')])
for name in ('Server_BraceStart','Server_BraceStop','Server_ToggleView','Server_ToggleHeadlamp','Server_RequestBoost'):
    BP.add_event(character,name)
for name,cls in [('Health',health.generated_class()),('PlayerView',view.generated_class())]:
    comp,handle = component(character,name,cls)
    comp.set_is_replicated(True)
headlamp,handle = component(character,'Headlamp',ue.SpotLightComponent)
headlamp.set_editor_property('relative_location',ue.Vector(0,0,65))
headlamp.set_editor_property('intensity',0.0)
headlamp.set_editor_property('attenuation_radius',1800.0)
headlamp.set_editor_property('inner_cone_angle',16.0)
headlamp.set_editor_property('outer_cone_angle',28.0)
headlamp.set_editor_property('cast_shadows',False)
headlamp.set_editor_property('mobility',ue.ComponentMobility.MOVABLE)
compile_bp(character)

pc = ue.load_asset('/Game/Core/BP_CoopPlayerController')
var(pc,'RunInputAdded','bool',False)
var(pc,'SecondaryMove','Vector2D',ue.Vector2D())
var(pc,'SecondaryLook','Vector2D',ue.Vector2D())
for name in ('AdventureControllerBegin','AdventureControllerEnd','SetupRunInput','RemoveRunInput','HostAddLocalPlayer','HostRemoveLocalPlayer','RequestRunRestart','RefreshSplitKeyboard'):
    fn(pc,name)
fn(pc,'ResolveSecondaryLocalPawn',outputs=[('SecondaryPawn',ue.Pawn.static_class())])
compile_bp(pc)

gi = ue.load_asset('/Game/Core/BP_CoopGameInstance')
for n,t,val in [('RunActive','bool',False),('RunStage','int',0),('RunPrefixCollected','int',0),('RunPrefixAvailable','int',0),('HostLocalCount','int',1),('RestoreLocalPending','bool',False)]:
    var(gi,n,t,val)
compile_bp(gi)
gs = ue.load_asset('/Game/Core/BP_CoopGameState')
var(gs,'AreaName','string','Cave',replicated=True)
var(gs,'AdventureInstruction','string','Join your team, then stand on the start pad.',replicated=True)
compile_bp(gs)

RESULT={'health':health.get_path_name(),'view':view.get_path_name(),'scaffolded_core':[character.get_path_name(),pc.get_path_name(),gi.get_path_name(),gs.get_path_name()],'rpc_events_require_server_flags':5,'shipping_logic_written':False}
(QUEUE/'player-scaffold.json').write_text(json.dumps(RESULT,indent=2))
