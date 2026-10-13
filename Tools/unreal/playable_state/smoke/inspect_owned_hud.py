"""Parent-only read-only host split HUD/view snapshot; no actor/input setters.

Run after root's disclosed CreatePlayer fixture has settled two host-local
owners in network PIE. ARGS report_name labels before/after; require_geometry
opts into a painted cached-bounds gate. No pixel/render acceptance is inferred.
"""
import json,re,sys,traceback
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from Tools.unreal.playable_state.smoke.context import ROOT,QUEUE
EXPECTED=ROOT
args=globals().get('ARGS',{});name=args.get('report_name','hud-owned-snapshot')
assert re.fullmatch(r'[A-Za-z0-9_-]+',name)
OUT=QUEUE/(name+'.json')
RESULT={'passed':False,'read_only':True,'rendered_pixel_acceptance':False,'native_log_scan_pending':True,'owners':[],'geometry_not_painted':[]}
try:
    assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
    worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));servers=[w for w in worlds if ue.GameplayStatics.get_game_mode(w)]
    assert len(servers)==1;server=servers[0]
    C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
    HC=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
    WC=ue.load_asset('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD').generated_class()
    PC=ue.load_asset('/Game/Puzzles/UI/WBP_InteractPrompt').generated_class()
    H=ue.load_asset('/Game/Hazards/AC_Health').generated_class()
    U=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class()
    V=ue.load_asset('/Game/Player/AC_PlayerView').generated_class()
    host=[p for p in ue.GameplayStatics.get_all_actors_of_class(server,C) if p.is_locally_controlled()]
    assert len(host)==2,'Require two actual settled host-local owners; parent may CreatePlayer as a disclosed fixture'
    assert sum(p.get_controller().is_primary_player() for p in host)==1
    active=[w for w in ue.ObjectIterator(ue.UserWidget) if w.get_class() in (WC,PC) and w.is_in_viewport()]
    all_owners=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()]
    assert len(all_owners) in (2,3,4)
    hud_names=[];prompt_names=[]
    for p in all_owners:
        pc=p.get_controller();pid=p.player_state.player_id;components=p.get_components_by_class(HC)
        assert len(components)==1
        hud=components[0];widget=hud.get_editor_property('HUDWidget');prompt=p.get_editor_property('PromptWidget')
        assert widget and widget.is_in_viewport() and widget.get_owning_player()==pc and hud.get_editor_property('HUDController')==pc
        assert prompt and prompt.is_in_viewport() and prompt.get_owning_player()==pc
        assert len([w for w in active if w.get_class()==WC and w.get_owning_player()==pc])==1
        assert len([w for w in active if w.get_class()==PC and w.get_owning_player()==pc])==1
        dead=bool(p.get_component_by_class(H).call_method('IsDead'));stock=p.get_component_by_class(U).get_editor_property('FlaresLeft')
        view=p.get_component_by_class(V);target=view.get_editor_property('SpectatedPawn')
        assert widget.get_editor_property('DisplayedDead')==dead
        assert widget.get_editor_property('DisplayedFlares')==stock
        if dead and target:
            assert not target.get_component_by_class(H).call_method('IsDead')
            assert pc.get_view_target()==target,'Wait until the normal spectator camera blend finishes'
            slot=view.get_editor_property('LastSpectatorSlot')
            assert f'watching P{slot+1}' in widget.get_editor_property('DisplaySpectator')
        elif not dead:assert pc.get_view_target()==p,'Living owner lost its view target'
        player_geo=ue.WidgetLayoutLibrary.get_player_screen_widget_geometry(pc)
        screen=ue.SlateLibrary.get_local_size(player_geo);cached=ue.SlateLibrary.get_local_size(widget.get_cached_geometry())
        painted=screen.x>100 and screen.y>100 and cached.x>100 and cached.y>100
        if painted:
            assert abs(cached.x-screen.x)<max(4,screen.x*.03) and abs(cached.y-screen.y)<max(4,screen.y*.03)
        else:RESULT['geometry_not_painted'].append(pid)
        hud_names.append(widget.get_path_name());prompt_names.append(prompt.get_path_name())
        RESULT['owners'].append({'id':pid,'host_local':p.get_world()==server,'primary':pc.is_primary_player(),
            'controller':pc.get_path_name(),'hud':widget.get_path_name(),'prompt':prompt.get_path_name(),
            'dead':dead,'flares':stock,'view_target':pc.get_view_target().get_path_name() if pc.get_view_target() else None,
            'spectated_slot':view.get_editor_property('LastSpectatorSlot'),
            'round_name':widget.get_editor_property('DisplayRoundName'),'objective':widget.get_editor_property('DisplayObjective'),
            'team':widget.get_editor_property('DisplayTeam'),'tools':widget.get_editor_property('DisplayTools'),
            'spectator':widget.get_editor_property('DisplaySpectator'),'show_hud':widget.get_editor_property('ShowSixHUD'),
            'screen_size':[screen.x,screen.y],'cached_hud_size':[cached.x,cached.y]})
    assert len(set(hud_names))==len(set(prompt_names))==len(all_owners)
    if args.get('require_geometry'):assert not RESULT['geometry_not_painted'],'Geometry gate needs painted player widgets'
    RESULT['geometry_qualified']=not RESULT['geometry_not_painted'];RESULT['passed']=True
except Exception:RESULT['error']=traceback.format_exc()
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(RESULT,indent=2))
