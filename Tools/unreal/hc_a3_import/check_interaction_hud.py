import json,time,traceback
from pathlib import Path
import unreal

root=Path(unreal.Paths.project_saved_dir())/'HCA3'
expected=int((root/'clients.txt').read_text())
report={'ok':False,'clients':expected,'checks':[]}
stage=0
next_check=0
deadline=time.monotonic()+180
handle=None
pawn=None
worlds=[]
lane=None
mode=0

def action(name):
    unreal.SystemLibrary.set_timer(pawn,name,0.02,False)

def targets(kind):
    return {w.get_path_name():next(a for a in unreal.GameplayStatics.get_all_actors_with_tag(w,'HC1_'+kind) if lane in [str(t) for t in a.tags]) for w in worlds}

def count(kind,name):
    return [a.get_editor_property(name) for a in targets(kind).values()]

def focus(kind):
    target=targets(kind)[pawn.get_world().get_path_name()]
    pid=pawn.player_state.get_editor_property('PlayerId')
    location=target.get_actor_location()+unreal.Vector(-250,0,-8)
    for w in worlds:
        for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character):
            if a.player_state.get_editor_property('PlayerId')==pid:
                a.set_actor_location(location,False,True)
                if a.get_controller(): a.get_controller().set_control_rotation(unreal.Rotator(0,0,0))
        # Keep other fixtures from occluding this isolated interaction scenario.
        for a in unreal.GameplayStatics.get_all_actors_with_tag(w,'HC1Lane_'+lane.split('_')[-1]):
            a.set_actor_enable_collision(a==targets(kind)[w.get_path_name()])
    return target

def finish(ok,error=None):
    report['ok']=ok
    if error:report['error']=error
    (Path(unreal.Paths.project_dir())/'SourceArt/HC/HC-A3/integration'/f'client-interaction-{expected}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.log(f'HC1_ACCEPTANCE_{expected}_COMPLETE: {ok}')

def tick(dt):
    global stage,next_check,pawn,worlds,lane
    try:
        now=time.monotonic()
        assert now<deadline,'Acceptance timed out'
        if now<next_check:return
        if stage==0:
            worlds=list(unreal.EditorLevelLibrary.get_pie_worlds(True))
            if len(worlds)!=expected+1:return
            states=[unreal.GameplayStatics.get_game_state(w) for w in worlds]
            if any(s is None or s.call_method('GetPlayerCount')!=expected for s in states):return
            local=[p for w in worlds for p in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character) if p.is_locally_controlled()]
            if len(local)!=expected or not all(p.get_editor_property('InputReady') for p in local):return
            for p in local:
                widget=p.get_editor_property('PromptWidget')
                assert widget and widget.get_owning_player()==p.get_controller()
            component_class=unreal.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
            hud_components=[p.get_component_by_class(component_class) for p in local]
            if any(c is None or c.get_editor_property('HUDWidget') is None for c in hud_components):return
            hud_widgets=[c.get_editor_property('HUDWidget') for c in hud_components]
            assert len(set(widget.get_path_name() for widget in hud_widgets))==expected
            assert all(widget.get_owning_player()==p.get_controller() for p,widget in zip(local,hud_widgets))
            assert all(c.get_editor_property('HUDController')==p.get_controller() for p,c in zip(local,hud_components))
            report['checks'].append({'hca3_owned_hud_instances':expected,'hca3_controller_binding':True})
            pawn=local[0]
            target=pawn.get_editor_property('FocusedTarget')
            if not target:return
            lane=next(str(t) for t in target.tags if str(t).startswith('HC1Lane_'))
            assert 'HC1_Instant' in [str(t) for t in target.tags]
            report['checks'].append({'per_player_input_ready':expected,'widgets_have_owning_controller':True,'focus_trace_found_instant':True})
            action('PressInteract')
            stage=1;next_check=now+1.5
        elif stage==1:
            if count('Instant','InstantCount')!=[1]*len(worlds): return
            assert count('Instant','InstantCount')==[1]*len(worlds),count('Instant','InstantCount')
            action('ReleaseInteract')
            report['checks'].append({'instant_rpc_and_replication':True})
            focus('Timed');stage=2;next_check=now+1.5
        elif stage==2:
            assert pawn.get_editor_property('FocusedTarget')==targets('Timed')[pawn.get_world().get_path_name()]
            action('PressInteract');stage=3;next_check=now+.5
        elif stage==3:
            action('ReleaseInteract');stage=4;next_check=now+2.5
        elif stage==4:
            assert count('Timed','InstantCount')==[0]*len(worlds),count('Timed','InstantCount')
            report['checks'].append({'short_hold_cannot_complete':True})
            action('PressInteract');stage=5;next_check=now+2.8
        elif stage==5:
            assert count('Timed','InstantCount')==[1]*len(worlds),count('Timed','InstantCount')
            action('ReleaseInteract')
            report['checks'].append({'full_server_timed_hold_and_replication':True})
            focus('Continuous');stage=6;next_check=now+1.5
        elif stage==6:
            assert pawn.get_editor_property('FocusedTarget')==targets('Continuous')[pawn.get_world().get_path_name()]
            action('PressInteract');stage=7;next_check=now+1.5
        elif stage==7:
            assert count('Continuous','BeginCount')==[1]*len(worlds),count('Continuous','BeginCount')
            assert count('Continuous','ActiveUsers')==[1]*len(worlds)
            action('ReleaseInteract');stage=8;next_check=now+1.5
        elif stage==8:
            assert count('Continuous','EndCount')==[1]*len(worlds),count('Continuous','EndCount')
            assert count('Continuous','ActiveUsers')==[0]*len(worlds)
            report['checks'].append({'continuous_begin_end_replicated':True})
            action('PressInteract');stage=9;next_check=now+1.5
        elif stage==9:
            assert count('Continuous','BeginCount')==[2]*len(worlds)
            pid=pawn.player_state.get_editor_property('PlayerId')
            for w in worlds:
                for p in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character):
                    if p.player_state.get_editor_property('PlayerId')==pid:
                        p.set_actor_location(p.get_actor_location()+unreal.Vector(2000,0,0),False,True)
            stage=10;next_check=now+2
        elif stage==10:
            assert count('Continuous','EndCount')==[2]*len(worlds),count('Continuous','EndCount')
            assert count('Continuous','ActiveUsers')==[0]*len(worlds)
            report['checks'].append({'out_of_range_cancels_continuous_use':True})
            action('ReleaseInteract');focus('Continuous');stage=11;next_check=now+1.5
        elif stage==11:
            action('PressInteract');stage=12;next_check=now+1.5
        elif stage==12:
            assert count('Continuous','BeginCount')==[3]*len(worlds)
            server=next(w for w in worlds if unreal.GameplayStatics.get_game_mode(w))
            targets('Continuous')[server.get_path_name()].set_editor_property('InteractionEnabled',False)
            stage=13;next_check=now+2
        elif stage==13:
            assert count('Continuous','EndCount')==[3]*len(worlds),count('Continuous','EndCount')
            assert count('Continuous','ActiveUsers')==[0]*len(worlds)
            report['checks'].append({'can_interact_becoming_false_cancels_use':True})
            action('ReleaseInteract')
            server=next(w for w in worlds if unreal.GameplayStatics.get_game_mode(w))
            targets('Continuous')[server.get_path_name()].set_editor_property('InteractionEnabled',True)
            stage=14;next_check=now+2
        elif stage==14:
            action('PressInteract');stage=15;next_check=now+1.5
        elif stage==15:
            assert count('Continuous','BeginCount')==[4]*len(worlds)
            server=next(w for w in worlds if unreal.GameplayStatics.get_game_mode(w))
            unreal.SystemLibrary.set_timer(targets('Continuous')[server.get_path_name()],'TestStartRound',0.02,False)
            stage=16;next_check=now+2
        elif stage==16:
            assert count('Continuous','EndCount')==[4]*len(worlds),count('Continuous','EndCount')
            assert count('Continuous','ActiveUsers')==[0]*len(worlds)
            from editor_toolset.toolsets.object import ObjectTools
            rounds=[json.loads(ObjectTools.get_properties(unreal.GameplayStatics.get_game_state(w),['RoundState']))['RoundState'] for w in worlds]
            assert all(r['index']==1 and r['phase']=='Playing' and r['attempt']==1 for r in rounds),rounds
            report['checks'].append({'round_start_cancels_active_use_and_replicates_struct':True})
            action('ReleaseInteract');focus('Continuous');stage=17;next_check=now+2
        elif stage==17:
            action('PressInteract');stage=18;next_check=now+1.5
        elif stage==18:
            assert count('Continuous','BeginCount')==[5]*len(worlds),(count('Continuous','BeginCount'),str(pawn.get_editor_property('FocusedTarget')))
            pid=pawn.player_state.get_editor_property('PlayerId')
            server=next(w for w in worlds if unreal.GameplayStatics.get_game_mode(w))
            authoritative=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.Character) if p.player_state.get_editor_property('PlayerId')==pid)
            authoritative.destroy_actor()
            stage=19;next_check=now+2
        elif stage==19:
            assert count('Continuous','EndCount')==[5]*len(worlds),count('Continuous','EndCount')
            assert count('Continuous','ActiveUsers')==[0]*len(worlds)
            report['checks'].append({'pawn_end_play_releases_continuous_use':True})
            finish(True)
    except Exception:finish(False,traceback.format_exc())

handle=unreal.register_slate_post_tick_callback(tick)
unreal.log(f'HC1_ACCEPTANCE_{expected}_ARMED')
