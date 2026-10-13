"""Parent-only one-shot read-only UMG/viewport diagnostic, version 2.

Loaded native classes avoid missing Python aliases. User-visible schema is
checked before ObjectTools reads; protected plain UPROPERTY is not bypassed.
Exact local players come from existing owning Enhanced Input subsystems.
No asset changes, inputs, widget creation, PIE lifecycle or console setters.
"""
import json
import re
import time
import traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ

EXPECTED=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
args=globals().get('ARGS',{})
name=args.get('report_name','hud-viewport-v2')
assert re.fullmatch(r'[A-Za-z0-9_-]+',name)
OUT=Path('/tmp/coop-audit/runtime-evidence')/(name+'.json')
R={'schema':2,'read_only':True,'collection_complete':False,
   'ownership_geometry_gate_passed':False,'rendered_pixel_acceptance':False,
   'native_log_scan_pending':True,'owners':[],'viewport_clients':[],
   'local_players':[],'native_read_errors':[],'limitations':[
       'No direct Slate SWidget/GameLayerManager/window pointers are exposed by these reads.',
       'Plain UPROPERTY without Edit/BlueprintVisible/BlueprintAssignable is not readable through ObjectTools.',
       'Viewport matched by its public world context is a candidate; this is not a direct read of LocalPlayer.ViewportClient.',
       'Collection completion is not a geometry or pixel acceptance pass.']}
start=time.monotonic()
schema_cache={}

def ref(obj):return obj.get_path_name() if obj is not None else None

def vec(v):return [float(v.x),float(v.y)]

def size(g):return vec(ue.SlateLibrary.get_local_size(g))

def prop(obj,name):return obj.get_editor_property(name)

def attempt(label,fn):
    try:return fn()
    except Exception as exc:
        R['native_read_errors'].append({'read':label,'type':type(exc).__name__,'error':str(exc)})
        return None

def norm(s):return str(s).replace('_','').lower()

def listed_reads(obj,names):
    """Only ask native ObjectTools for names its user-visible schema listed."""
    key=ref(obj.get_class())
    if key not in schema_cache:
        data=json.loads(OBJ.list_properties(obj))
        assert isinstance(data,dict),'ObjectTools schema must be a JSON object'
        schema_cache[key]=data.get('properties',data)
    keys=schema_cache[key]
    chosen={name:next((k for k in keys if norm(k)==norm(name)),None) for name in names}
    read_names=[k for k in chosen.values() if k is not None]
    values=json.loads(OBJ.get_properties(obj,read_names)) if read_names else {}
    return {'requested':list(names),'schema_listed':read_names,
        'unavailable_not_in_user_visible_schema':[name for name,k in chosen.items() if k is None],
        'values':values}

def anchors(a):return {'minimum':vec(a.minimum),'maximum':vec(a.maximum)}

def slot(s):
    o=s.offsets
    return {'anchors':anchors(s.anchors),'offsets':{'left':float(o.left),'top':float(o.top),'right':float(o.right),'bottom':float(o.bottom)},
        'alignment':vec(s.alignment),'z_order':int(s.z_order),'auto_remove_on_world_removed':bool(s.auto_remove_on_world_removed)}

def widget_row(w,label,subsystem,pc):
    if w is None:return None
    def read(key,fn):return attempt(label+'.'+key,fn)
    return {'path':ref(w),'class':ref(w.get_class()),'owning_controller':ref(w.get_owning_player()),
        'owning_controller_matches':w.get_owning_player()==pc,'world':ref(w.get_world()),
        'game_instance':ref(ue.GameplayStatics.get_game_instance(w)),
        'is_in_viewport':w.is_in_viewport(),'subsystem_widget_added':subsystem.is_widget_added(w),
        'visibility':str(w.get_visibility()),'render_opacity':float(w.get_render_opacity()),
        'desired_size':vec(w.get_desired_size()),'cached_size':size(w.get_cached_geometry()),
        'paint_space_size':size(w.get_paint_space_geometry()),'tick_space_size':size(w.get_tick_space_geometry()),
        'anchors_in_viewport':anchors(w.get_anchors_in_viewport()),'alignment_in_viewport':vec(w.get_alignment_in_viewport()),
        'game_viewport_slot':slot(subsystem.get_widget_slot(w)),
        'instance_optional_native_paint_flag':read('instance_optional_native_paint_flag',lambda:listed_reads(w,['bHasScriptImplementedPaint'])),
        'cdo_optional_native_paint_flag':read('cdo_optional_native_paint_flag',lambda:listed_reads(ue.get_default_object(w.get_class()),['bHasScriptImplementedPaint']))}

try:
    assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
    worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert 1<=len(worlds)<=5
    C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
    HC=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
    owners=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()]
    assert len(owners) in (2,3,4) and len({p.player_state.player_id for p in owners})==len(owners)
    R['engine']=ue.SystemLibrary.get_engine_version()
    R['worlds']=[{'world':ref(w),'has_authoritative_game_mode':bool(ue.GameplayStatics.get_game_mode(w))} for w in worlds]
    sub=ue.get_engine_subsystem(ue.GameViewportSubsystem);assert sub
    library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary');assert library
    VC=ue.load_class(None,'/Script/Engine.GameViewportClient');LP=ue.load_class(None,'/Script/Engine.LocalPlayer')
    assert VC and LP and ref(VC)=='/Script/Engine.GameViewportClient' and ref(LP)=='/Script/Engine.LocalPlayer'
    R['loaded_native_classes']={'viewport':ref(VC),'local_player':ref(LP)}
    viewport_objects=[];player_objects=[]
    for i,vc in enumerate(ue.ObjectIterator(VC)):
        assert time.monotonic()-start<10,'Diagnostic exceeded ten-second bound'
        if i>=16:R['viewport_inventory_truncated']=True;break
        world=vc.get_world()
        if world not in worlds:continue
        gi=ue.GameplayStatics.get_game_instance(vc)
        viewport_objects.append((vc,world,gi))
        R['viewport_clients'].append({'path':ref(vc),'class':ref(vc.get_class()),'world':ref(world),'game_instance':ref(gi),
            'pixel_size':vec(ue.WidgetLayoutLibrary.get_viewport_size(vc)),
            'widget_host_size':size(ue.WidgetLayoutLibrary.get_viewport_widget_geometry(vc)),
            'optional_reflected_relationships':attempt('viewport'+str(i)+'.optional_reflected_relationships',lambda:listed_reads(vc,['World','GameInstance']))})
    for i,lp in enumerate(ue.ObjectIterator(LP)):
        assert time.monotonic()-start<10,'Diagnostic exceeded ten-second bound'
        if i>=16:R['local_player_inventory_truncated']=True;break
        world=lp.get_world()
        if world not in worlds:continue
        player_objects.append(lp)
        R['local_players'].append({'path':ref(lp),'class':ref(lp.get_class()),'world':ref(world),'outer':ref(lp.get_outer()),
            'optional_reflected_relationships':attempt('local_player'+str(i)+'.optional_reflected_relationships',lambda:listed_reads(lp,['ViewportClient','ViewportClientOverride','PlayerController']))})
    for p in owners:
        assert time.monotonic()-start<10,'Diagnostic exceeded ten-second bound'
        pc=p.get_controller();pid=p.player_state.player_id;label='owner'+str(pid);world=p.get_world()
        gi=ue.GameplayStatics.get_game_instance(pc)
        input_subsystem=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(pc,ue.EnhancedInputLocalPlayerSubsystem.static_class()))
        assert input_subsystem,'Existing owning Enhanced Input subsystem required'
        lp=input_subsystem.get_outer();assert lp.get_class().get_path_name()=='/Script/Engine.LocalPlayer' or lp in player_objects
        hc=p.get_components_by_class(HC);hud=prop(hc[0],'HUDWidget') if len(hc)==1 else None;prompt=prop(p,'PromptWidget')
        row={'id':pid,'primary':pc.is_primary_player(),'pawn':ref(p),'controller':ref(pc),'world':ref(world),'game_instance':ref(gi),
            'exact_local_player':ref(lp),'local_player_derivation':'Existing GetLocalPlayerSubSystemFromPlayerController result -> Within=LocalPlayer outer',
            'local_player_subsystem':ref(input_subsystem),'local_player_world':ref(lp.get_world()),'local_player_world_matches':lp.get_world()==world,
            'local_player_outer':ref(lp.get_outer()),'local_player_outer_matches_game_instance':lp.get_outer()==gi,
            'local_players_in_game_instance_by_outer':[ref(x) for x in player_objects if x.get_outer()==gi],
            'exact_local_player_in_filtered_native_inventory':lp in player_objects,
            'viewport_candidates_matching_world':[ref(vc) for vc,vw,vgi in viewport_objects if vw==world],
            'viewport_candidates_matching_world_and_game_instance':[ref(vc) for vc,vw,vgi in viewport_objects if vw==world and vgi==gi],
            'controller_optional_player_property':attempt(label+'.controller_optional_player_property',lambda:listed_reads(pc,['Player'])),
            'game_instance_optional_local_players_property':attempt(label+'.game_instance_optional_local_players_property',lambda:listed_reads(gi,['LocalPlayers'])),
            'controller_viewport_pixel_size':list(pc.get_viewport_size()),'context_viewport_pixel_size':vec(ue.WidgetLayoutLibrary.get_viewport_size(pc)),
            'context_viewport_scale':float(ue.WidgetLayoutLibrary.get_viewport_scale(pc)),
            'viewport_widget_host_size':size(ue.WidgetLayoutLibrary.get_viewport_widget_geometry(pc)),
            'player_widget_host_size':size(ue.WidgetLayoutLibrary.get_player_screen_widget_geometry(pc)),
            'hud_component_count':len(hc),'hud':widget_row(hud,label+'.hud',sub,pc),'prompt':widget_row(prompt,label+'.prompt',sub,pc)}
        if hud:row['show_six_hud']=bool(prop(hud,'ShowSixHUD'));row['displayed_flares']=int(prop(hud,'DisplayedFlares'))
        R['owners'].append(row)
    R['schema_queried_classes']=list(schema_cache)
    R['collection_complete']=True
except Exception:R['error']=traceback.format_exc()
R['elapsed_seconds']=round(time.monotonic()-start,4)
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(R,indent=2))
