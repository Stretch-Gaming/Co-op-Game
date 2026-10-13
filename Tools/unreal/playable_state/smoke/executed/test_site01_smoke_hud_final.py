"""Parent-only L_Site01 Play As Client2 smoke, normal spawn and owning input.

Parent loads /Game/Maps/L_Site01, starts settled PIE_Client with2 players and
Run Under One Process, runs this file serially, scans the native log, stops PIE
and restores preferences. No map/PIE/settings/asset/world-state setters here.
Movement and V/F use the real owning Enhanced Input/RPC path. No builder calls,
approach teleports, health/round/stock setters, old fixture-marker assertions,
or player-index gameplay getters. Output is outside the repository.
"""
import json,sys,time,traceback
from pathlib import Path
import unreal as ue
EXPECTED=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
REPORT=Path('/tmp/coop-audit/runtime-evidence/site01-client2-smoke-hud-final.json')

def run():
    assert Path(ue.Paths.project_dir()).resolve()==EXPECTED, 'Wrong editor project'
    sys.path.insert(0,str(EXPECTED))
    from Tools.unreal.playable_state.ghosts.ghost_runtime_support import Harness
    args=dict(globals().get('ARGS',{}));args.update(players=2,profile='joining');args.setdefault('timeout',35)
    h=Harness(args,'site01-client2-smoke');h.report=REPORT
    assert len(h.worlds)==3 and len(h.locals)==2
    assert all(ue.GameplayStatics.get_current_level_name(w,True)=='L_Site01' for w in h.worlds)
    HUD=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
    HUD_WIDGET=ue.load_asset('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD').generated_class()
    PROMPT=ue.load_asset('/Game/Puzzles/UI/WBP_InteractPrompt').generated_class()
    state={'owner_index':0,'moves':[],'initial_ui':None,'initial_view':{},'initial_lamp':{},'camera':{},'positions':{},'observations':[]}
    original_finish=h.finish
    def finish(ok,error=None):
        result=original_finish(ok,error)
        if result:
            result.update(map='L_Site01',method='Normal spawning; owning movement and V/F input; no gameplay-state fixtures.',
                movements=state['moves'],ui_observations=state['observations'],native_log_scan_pending=True,
                full_mission_acceptance=False,rendered_pixel_acceptance=False)
            REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(result,indent=2))
        return result
    h.finish=finish
    def pawn(pid):return h.pawn(h.server,pid)
    def floor_check():
        for pid in h.ids:
            p=pawn(pid);m=p.character_movement
            assert not h.prop(p,'health','bDead'), ('Fresh smoke player died',pid)
            assert m.is_moving_on_ground() and m.movement_mode==ue.MovementMode.MOVE_WALKING, ('No normal-spawn floor support',pid,str(p.get_actor_location()),str(m.movement_mode))
            assert p.get_actor_location().z>-100, ('Normal-spawn pawn below cave floor',pid)
    def ui_check():
        active=[w for w in ue.ObjectIterator(ue.UserWidget) if w.get_class() in (HUD_WIDGET,PROMPT) and w.is_in_viewport()]
        rows=[];widget_ids=[];prompt_ids=[]
        for pid in h.ids:
            p=h.locals[pid];pc=p.get_controller();components=p.get_components_by_class(HUD)
            assert len(components)==1, ('Duplicate HUD components',pid,len(components))
            component=components[0];widget=component.get_editor_property('HUDWidget');prompt=p.get_editor_property('PromptWidget')
            assert widget and widget.is_in_viewport() and widget.get_owning_player()==pc
            assert component.get_editor_property('HUDController')==pc
            assert prompt and prompt.is_in_viewport() and prompt.get_owning_player()==pc
            hud_count=len([w for w in active if w.get_class()==HUD_WIDGET and w.get_owning_player()==pc])
            prompt_count=len([w for w in active if w.get_class()==PROMPT and w.get_owning_player()==pc])
            assert hud_count==prompt_count==1, ('Duplicate active owner widgets',pid,hud_count,prompt_count)
            assert widget.get_editor_property('DisplayedFlares')==h.prop(p,'tools','FlaresLeft')
            assert widget.get_editor_property('DisplayedDead')==h.prop(p,'health','bDead')
            prefix='LAMP ON' if h.prop(p,'view','bHeadlampOn') else 'LAMP OFF'
            assert widget.get_editor_property('DisplayTools').startswith(prefix), ('Tool HUD copied another owner lamp state',pid)
            widget_ids.append(widget.get_path_name());prompt_ids.append(prompt.get_path_name())
            rows.append({'id':pid,'controller':pc.get_path_name(),'hud':widget.get_path_name(),'prompt':prompt.get_path_name(),
                         'active_hud_count':hud_count,'active_prompt_count':prompt_count,
                         'objective':widget.get_editor_property('DisplayObjective'),'dead':widget.get_editor_property('DisplayedDead'),
                         'flares':widget.get_editor_property('DisplayedFlares'),'tools':widget.get_editor_property('DisplayTools')})
        assert len(set(widget_ids))==len(set(prompt_ids))==2, 'Owners share a HUD or prompt instance'
        state['observations'].append(rows)
        return rows
    def tick(_delta):
        elapsed=h.elapsed()
        if h.phase=='warmup' and elapsed>1.5:
            floor_check();state['initial_ui']=ui_check()
            for pid in h.ids:
                p=h.locals[pid]
                assert p.get_editor_property('InputReady') and p.get_editor_property('SixInputReady')
                state['initial_view'][pid]=h.prop(pawn(pid),'view','ViewMode')
                state['initial_lamp'][pid]=h.prop(pawn(pid),'view','bHeadlampOn')
                state['camera'][pid]=(p.get_component_by_class(ue.SpringArmComponent).target_arm_length,p.get_component_by_class(ue.CameraComponent).field_of_view)
            h.check('Two joining owners have distinct single active HUD/prompt instances and normal-spawn floor support')
            state['positions']={i:pawn(i).get_actor_location() for i in h.ids}
            h.hold(h.ids[0],'move',ue.Vector(0,1,0));h.transition('move')
        elif h.phase=='move':
            pid=h.ids[state['owner_index']]
            if elapsed>.35:h.release(pid,'move')
            if elapsed>1.05:
                floor_check()
                distance=(pawn(pid).get_actor_location()-state['positions'][pid]).length()
                assert distance>20, ('Owning movement did not move pawn from normal spawn',pid,distance)
                for other in h.ids:
                    if other!=pid:assert (pawn(other).get_actor_location()-state['positions'][other]).length()<10, ('One owner moved another pawn',pid,other)
                for w in h.worlds:
                    assert (h.pawn(w,pid).get_actor_location()-pawn(pid).get_actor_location()).length()<80, 'Client movement did not reach a peer'
                state['moves'].append({'id':pid,'distance_cm':distance,'on_ground':True})
                h.check('Owning client movement reaches server/peers and leaves other pawn stationary',{'id':pid,'distance_cm':distance})
                state['owner_index']+=1
                if state['owner_index']<2:
                    state['positions']={i:pawn(i).get_actor_location() for i in h.ids}
                    h.hold(h.ids[state['owner_index']],'move',ue.Vector(0,1,0));h.transition('move')
                else:
                    state['owner_index']=0;h.hold(h.ids[0],'view');h.hold(h.ids[0],'lamp');h.transition('toggle')
        elif h.phase=='toggle':
            pid=h.ids[state['owner_index']]
            if elapsed>.15:h.release(pid,'view');h.release(pid,'lamp')
            if elapsed>1:
                for w in h.worlds:
                    for other in h.ids:
                        changed=h.ids.index(other)<=state['owner_index']
                        mode=h.prop(h.pawn(w,other),'view','ViewMode');lamp=h.prop(h.pawn(w,other),'view','bHeadlampOn')
                        assert (mode!=state['initial_view'][other]) if changed else (mode==state['initial_view'][other])
                        assert (lamp!=state['initial_lamp'][other]) if changed else (lamp==state['initial_lamp'][other])
                p=h.locals[pid];camera=(p.get_component_by_class(ue.SpringArmComponent).target_arm_length,p.get_component_by_class(ue.CameraComponent).field_of_view)
                assert abs(camera[0]-state['camera'][pid][0])>1 and abs(camera[1]-state['camera'][pid][1])>1, ('Owning V did not apply its camera',pid,camera,state['camera'][pid])
                if state['owner_index']==0:
                    other=h.ids[1];p=h.locals[other]
                    unchanged=(p.get_component_by_class(ue.SpringArmComponent).target_arm_length,p.get_component_by_class(ue.CameraComponent).field_of_view)
                    assert all(abs(a-b)<1 for a,b in zip(unchanged,state['camera'][other])), 'V changed another owning camera'
                ui_check();floor_check();h.check('Owning V/F reaches every peer and updates only the selected owner camera/tool HUD',{'id':pid})
                state['owner_index']+=1
                if state['owner_index']<2:
                    pid=h.ids[state['owner_index']];h.hold(pid,'view');h.hold(pid,'lamp');h.transition('toggle')
                else:h.finish(True)
    return h.register(tick)

try:RESULT=run()
except Exception:
    RESULT={'passed':False,'stage':'preflight','error':traceback.format_exc(),'map':'L_Site01','native_log_scan_pending':True}
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(RESULT,indent=2))
