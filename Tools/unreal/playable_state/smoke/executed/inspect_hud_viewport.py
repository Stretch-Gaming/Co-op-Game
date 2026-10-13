"""Parent-only bounded read-only HUD/viewport attachment diagnostic.

Run in settled network PIE after visible viewport paint frames. Does not start
PIE, create players/widgets, inject input, set properties or save packages.
Per-field unavailable reads are recorded; collection is never a visual pass.
"""
import json
import re
import time
import traceback
from pathlib import Path
import unreal as ue

EXPECTED=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
args=globals().get('ARGS',{})
name=args.get('report_name','hud-viewport-diagnostic')
assert re.fullmatch(r'[A-Za-z0-9_-]+',name)
OUT=Path('/tmp/coop-audit/runtime-evidence')/(name+'.json')
R={'schema':1,'read_only':True,'collection_complete':False,
   'ownership_geometry_gate_passed':False,'rendered_pixel_acceptance':False,
   'native_log_scan_pending':True,'owners':[],'viewport_clients':[],
   'native_read_errors':[],'limitations':[
       'No direct Slate SWidget/GameLayerManager/window pointers are exposed by these reads.',
       'A zero geometry does not identify which native GetPlayerScreenWidgetGeometry fallback branch occurred.',
       'Cached/paint geometry is a snapshot and requires several prior visible paint frames.',
       'No pixels, physical input or continuous route are qualified.']}
start=time.monotonic()

def ref(obj):
    return obj.get_path_name() if obj is not None else None

def vec(v):
    return [float(v.x),float(v.y)]

def size(g):
    return vec(ue.SlateLibrary.get_local_size(g))

def prop(obj,name):
    return obj.get_editor_property(name)

def attempt(label,fn):
    try:return fn()
    except Exception as exc:
        R['native_read_errors'].append({'read':label,'type':type(exc).__name__,'error':str(exc)})
        return None

def anchors(a):
    return {'minimum':vec(a.minimum),'maximum':vec(a.maximum)}

def slot(s):
    o=s.offsets
    return {'anchors':anchors(s.anchors),
            'offsets':{'left':float(o.left),'top':float(o.top),'right':float(o.right),'bottom':float(o.bottom)},
            'alignment':vec(s.alignment),'z_order':int(s.z_order),
            'auto_remove_on_world_removed':bool(s.auto_remove_on_world_removed)}

def widget_row(w,label,subsystem,pc):
    if w is None:return None
    def read(key,fn):return attempt(label+'.'+key,fn)
    return {'path':ref(w),'class':ref(w.get_class()),
        'owning_controller':read('owning_controller',lambda:ref(w.get_owning_player())),
        'owning_controller_matches':read('owning_controller_matches',lambda:w.get_owning_player()==pc),
        'world':read('world',lambda:ref(w.get_world())),
        'game_instance':read('game_instance',lambda:ref(ue.GameplayStatics.get_game_instance(w))),
        'outer':read('outer',lambda:ref(w.get_outer())),
        'is_in_viewport':read('is_in_viewport',w.is_in_viewport),
        'subsystem_widget_added':read('subsystem_widget_added',lambda:subsystem.is_widget_added(w)),
        'visibility':read('visibility',lambda:str(w.get_visibility())),
        'render_opacity':read('render_opacity',lambda:float(w.get_render_opacity())),
        'desired_size':read('desired_size',lambda:vec(w.get_desired_size())),
        'cached_size':read('cached_size',lambda:size(w.get_cached_geometry())),
        'paint_space_size':read('paint_space_size',lambda:size(w.get_paint_space_geometry())),
        'tick_space_size':read('tick_space_size',lambda:size(w.get_tick_space_geometry())),
        'anchors_in_viewport':read('anchors_in_viewport',lambda:anchors(w.get_anchors_in_viewport())),
        'alignment_in_viewport':read('alignment_in_viewport',lambda:vec(w.get_alignment_in_viewport())),
        'game_viewport_slot':read('game_viewport_slot',lambda:slot(subsystem.get_widget_slot(w))),
        'native_has_script_implemented_paint':read('native_has_script_implemented_paint',lambda:bool(prop(w,'bHasScriptImplementedPaint'))),
        'class_default_has_script_implemented_paint':read('class_default_has_script_implemented_paint',lambda:bool(prop(ue.get_default_object(w.get_class()),'bHasScriptImplementedPaint'))),
        'managed_by_game_viewport_subsystem':read('managed_by_game_viewport_subsystem',lambda:bool(prop(w,'bIsManagedByGameViewportSubsystem')))}

try:
    assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
    worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
    assert 1<=len(worlds)<=5,'Bounded network PIE only'
    C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
    HC=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
    owners=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()]
    assert len(owners) in (2,3,4),'Require settled two-to-four actual local input owners'
    assert len({p.player_state.player_id for p in owners})==len(owners)
    R['engine']=ue.SystemLibrary.get_engine_version()
    R['worlds']=[{'world':ref(w),'has_authoritative_game_mode':bool(ue.GameplayStatics.get_game_mode(w))} for w in worlds]
    sub=ue.get_engine_subsystem(ue.GameViewportSubsystem)
    assert sub,'GameViewportSubsystem unavailable'
    for p in owners:
        assert time.monotonic()-start<10,'Diagnostic exceeded ten-second bound'
        pc=p.get_controller();pid=p.player_state.player_id;label='owner'+str(pid)
        gi=ue.GameplayStatics.get_game_instance(pc)
        lp=attempt(label+'.controller_player',lambda:prop(pc,'Player'))
        vc=attempt(label+'.local_player_viewport',lambda:prop(lp,'ViewportClient')) if lp else None
        local_players=attempt(label+'.game_instance_local_players',lambda:list(prop(gi,'LocalPlayers')))
        hc=p.get_components_by_class(HC)
        hud=prop(hc[0],'HUDWidget') if len(hc)==1 else None
        prompt=prop(p,'PromptWidget')
        row={'id':pid,'primary':pc.is_primary_player(),'pawn':ref(p),'controller':ref(pc),'world':ref(p.get_world()),
             'game_instance':ref(gi),'local_player':ref(lp),'local_player_class':ref(lp.get_class()) if lp else None,
             'local_player_outer':attempt(label+'.local_player_outer',lambda:ref(lp.get_outer())) if lp else None,
             'local_player_controller_matches':attempt(label+'.local_player_controller_matches',lambda:prop(lp,'PlayerController')==pc) if lp else None,
             'game_instance_local_players':[ref(x) for x in local_players] if local_players is not None else None,
             'local_player_in_game_instance':lp in local_players if local_players is not None else None,
             'local_player_viewport_client':ref(vc),
             'viewport_client_world':attempt(label+'.viewport_client_world',lambda:ref(prop(vc,'World'))) if vc else None,
             'viewport_client_world_matches':attempt(label+'.viewport_client_world_matches',lambda:prop(vc,'World')==p.get_world()) if vc else None,
             'viewport_client_game_instance':attempt(label+'.viewport_client_game_instance',lambda:ref(prop(vc,'GameInstance'))) if vc else None,
             'viewport_client_game_instance_matches':attempt(label+'.viewport_client_game_instance_matches',lambda:prop(vc,'GameInstance')==gi) if vc else None,
             'viewport_client_override':attempt(label+'.viewport_client_override',lambda:ref(prop(lp,'ViewportClientOverride'))) if lp else None,
             'controller_viewport_pixel_size':attempt(label+'.controller_viewport_pixel_size',lambda:list(pc.get_viewport_size())),
             'context_viewport_pixel_size':attempt(label+'.context_viewport_pixel_size',lambda:vec(ue.WidgetLayoutLibrary.get_viewport_size(pc))),
             'context_viewport_scale':attempt(label+'.context_viewport_scale',lambda:float(ue.WidgetLayoutLibrary.get_viewport_scale(pc))),
             'viewport_widget_host_size':attempt(label+'.viewport_widget_host_size',lambda:size(ue.WidgetLayoutLibrary.get_viewport_widget_geometry(pc))),
             'player_widget_host_size':attempt(label+'.player_widget_host_size',lambda:size(ue.WidgetLayoutLibrary.get_player_screen_widget_geometry(pc))),
             'hud_component_count':len(hc),'hud':widget_row(hud,label+'.hud',sub,pc),
             'prompt':widget_row(prompt,label+'.prompt',sub,pc)}
        if hud:
            row['show_six_hud']=bool(prop(hud,'ShowSixHUD'))
            row['displayed_flares']=int(prop(hud,'DisplayedFlares'))
        R['owners'].append(row)
    for index,vc in enumerate(ue.ObjectIterator(ue.GameViewportClient)):
        if index>=16:
            R['viewport_inventory_truncated']=True;break
        world=attempt('viewport'+str(index)+'.world',lambda:prop(vc,'World'))
        if world not in worlds:continue
        R['viewport_clients'].append({'path':ref(vc),'world':ref(world),
            'game_instance':attempt('viewport'+str(index)+'.game_instance',lambda:ref(prop(vc,'GameInstance')))})
    R['collection_complete']=True
except Exception:
    R['error']=traceback.format_exc()
R['elapsed_seconds']=round(time.monotonic()-start,4)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(R,indent=2))
