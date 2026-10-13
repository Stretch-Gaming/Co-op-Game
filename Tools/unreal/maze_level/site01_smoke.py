"""Required unchanged Site01 joining-client HUD/input regression; no saves."""
import json,time,traceback,unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
old=json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_Client','PlayNumberOfClients':2,'RunUnderOneProcess':True}))
assert editor.load_level('/Game/Maps/L_Site01');editor.editor_request_begin_play()
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();HUD=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
lib=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary');action=ue.load_asset('/Game/Input/Actions/IA_Move')
state={'phase':'warm','at':time.monotonic()};report={'passed':False,'map':'/Game/Maps/L_Site01','mode':'Play As Client, two joining clients','checks':[]}
def input_for(p,value):
    sub=lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(p.get_controller(),ue.EnhancedInputLocalPlayerSubsystem.static_class()));assert sub
    sub.inject_input_vector_for_action(action,ue.Vector(0,value,0),[],[])
def finish(ok,error=None):
    report.update(passed=ok,error=error)
    for p in state.get('owners',[]):input_for(p,0)
    (QUEUE/'site01-smoke.json').write_text(json.dumps(report,indent=2));editor.editor_request_end_play();state.update(phase='closing',at=time.monotonic())
def tick(delta):
    try:
        worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));age=time.monotonic()-state['at']
        if state['phase']=='closing':
            if not worlds:OBJ.set_properties(settings,json.dumps(old));ue.unregister_slate_post_tick_callback(state['handle'])
            return
        assert age<25
        if state['phase']=='warm':
            if age<3:return
            owners=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled() and p.player_state]
            if len(owners)!=2:return
            assert all(not ue.SystemLibrary.is_server(p.get_world()) for p in owners)
            for p in owners:
                component=p.get_component_by_class(HUD);assert component
                widget=component.get_editor_property('HUDWidget');assert widget and widget.get_owning_player()==p.get_controller()
            state.update(owners=owners,starts=[p.get_actor_location() for p in owners],phase='move',at=time.monotonic())
            report['checks'].append('Two possessed joining clients in original Site01')
            report['checks'].append('Changed HUD remains owned by the correct local controller for both joining clients')
        elif state['phase']=='move':
            for p in state['owners']:input_for(p,.3 if age<.8 else 0)
            if age>1.1:
                report['owners']=[{'controller':p.get_controller().get_path_name(),'distance':(p.get_actor_location()-start).length()} for p,start in zip(state['owners'],state['starts'])]
                assert all(r['distance']>15 for r in report['owners'])
                report['checks'].append('Both owning Enhanced Input movement contexts respond in original Site01');finish(True)
    except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick);RESULT={'queued':str(QUEUE/'site01-smoke.json')}
