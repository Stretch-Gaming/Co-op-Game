"""Parent-only PIE fixture: reattach the eight existing owning HUD/prompt widgets.

Four settled host-split owners only. Capture all bounds, owners, data and full
viewport slots, remove/add the SAME widgets, restore saved slots, then observe
at most eight Slate post-tick callbacks or the five-second wall deadline.
A callback is not a proven paint frame. Positive paint geometry is required.
No players/widgets are created; no input, gameplay or asset properties change.
"""
import hashlib
import json
import re
import time
import traceback
from pathlib import Path
import unreal as ue

EXPECTED=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
SOURCE=Path('/tmp/coop-audit/probe_hud_reattach.py')
args=globals().get('ARGS',{})
name=args.get('report_name','hud-reattach')
assert re.fullmatch(r'[A-Za-z0-9_-]+',name)
OUT=Path('/tmp/coop-audit/runtime-evidence')/(name+'.json')
assert not OUT.exists(),'Archive the previous receipt or use a distinct report_name'
_ACTIVE_HUD_REATTACH=set()


def ref(o):return o.get_path_name() if o else None

def vec(v):return [float(v.x),float(v.y)]

def bounds(g):return vec(ue.SlateLibrary.get_local_size(g))

def positive(v):return len(v)==2 and all(x>1.0 for x in v)

def slot_data(s):
    a=s.anchors;o=s.offsets
    return {'anchors':{'minimum':vec(a.minimum),'maximum':vec(a.maximum)},
        'offsets':{'left':float(o.left),'top':float(o.top),'right':float(o.right),'bottom':float(o.bottom)},
        'alignment':vec(s.alignment),'z_order':int(s.z_order),
        'auto_remove_on_world_removed':bool(s.auto_remove_on_world_removed)}


class ReattachmentProbe:
    def __init__(self):
        self.handle=None;self.finished=False;self.entries=[];self.callbacks=0;self.started=time.monotonic()
        self.result={'schema':1,'status':'preflight','passed':False,'pie_only':True,
            'rendered_pixel_acceptance':False,'race_claim':False,'geometry_qualified':False,
            'nonzero_widget_paint_proof':False,'callback_limit':8,'wall_poll_limit_seconds':5,
            'callback_type':'unreal.register_slate_post_tick_callback; not an inferred paint frame',
            'native_log_scan_pending':True,'fixture_actions':[],'samples':[],
            'script_file':str(SOURCE),'script_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'limitations':['Geometry is native layout/paint readback, not pixel acceptance.',
                'A positive retry would demonstrate reattachment/layout behavior, not establish a startup race.',
                'Wall deadline is checked on each actual callback; a stalled editor requires parent cancellation.']}
        assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
        worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert len(worlds)==3,'Host plus two joining worlds required'
        server=[w for w in worlds if ue.GameplayStatics.get_game_mode(w)];assert len(server)==1
        self.server=server[0];assert ue.SystemLibrary.is_server(self.server) and not ue.SystemLibrary.is_dedicated_server(self.server)
        C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
        HC=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
        WC=ue.load_asset('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD').generated_class()
        PC=ue.load_asset('/Game/Puzzles/UI/WBP_InteractPrompt').generated_class()
        self.sub=ue.get_engine_subsystem(ue.GameViewportSubsystem);assert self.sub
        self.health=ue.load_asset('/Game/Hazards/AC_Health').generated_class()
        self.tools=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class()
        server_pawns=list(ue.GameplayStatics.get_all_actors_of_class(self.server,C));assert len(server_pawns)==4
        ids={p.player_state.player_id for p in server_pawns};assert len(ids)==4
        self.result['engine']=ue.SystemLibrary.get_engine_version()
        self.result['world_inventory']=[]
        for world in worlds:
            pawns=list(ue.GameplayStatics.get_all_actors_of_class(world,C))
            assert {p.player_state.player_id for p in pawns}==ids,'Roster must be settled on every peer'
            assert not ue.SystemLibrary.is_standalone(world)
            local=[p for p in pawns if p.is_locally_controlled()]
            assert len(local)==(2 if world==self.server else 1),'Two host owners and one owner on each joining peer required'
            self.result['world_inventory'].append({'world':ref(world),'host':world==self.server,'local_ids':[p.player_state.player_id for p in local]})
            for p in local:
                pc=p.get_controller();assert pc and pc.is_local_controller() and pc.get_world()==world
                assert p.get_editor_property('InputReady') and p.get_editor_property('SixInputReady')
                components=p.get_components_by_class(HC);assert len(components)==1
                component=components[0];hud=component.get_editor_property('HUDWidget');prompt=p.get_editor_property('PromptWidget')
                assert hud and prompt and hud.get_class()==WC and prompt.get_class()==PC
                assert component.get_editor_property('HUDController')==pc
                for widget in (hud,prompt):
                    assert widget.get_owning_player()==pc and widget.is_in_viewport() and self.sub.is_widget_added(widget)
                    assert self.sub.get_widget_slot(widget).z_order==0,'Fixture AddToPlayerScreen(0) must preserve existing z-order'
                self.entries.append({'id':p.player_state.player_id,'pawn':p,'pc':pc,'component':component,'hud':hud,'prompt':prompt,
                    'hud_slot':self.sub.get_widget_slot(hud),'prompt_slot':self.sub.get_widget_slot(prompt)})
        assert {e['id'] for e in self.entries}==ids
        host=[e for e in self.entries if e['pawn'].get_world()==self.server]
        assert len(host)==2 and sum(e['pc'].is_primary_player() for e in host)==1
        assert len({ref(e[k]) for e in self.entries for k in ('hud','prompt')})==8
        self.result['before']=self.snapshot()
        assert self.result['before']['unique_active_widgets']
        self.result['stage']='ready_to_reattach'
        self.write()

    def reattach(self):
        # Remove and immediately add each identical owning widget. Restoring its
        # saved viewport slot preserves prompt anchors, DPI offsets and alignment.
        for entry in self.entries:
            for key in ('hud','prompt'):
                widget=entry[key];original_slot=entry[key+'_slot']
                widget.remove_from_parent()
                try:
                    added=bool(widget.add_to_player_screen(0))
                finally:
                    self.sub.set_widget_slot(widget,original_slot)
                assert added and widget.get_owning_player()==entry['pc'] and widget.is_in_viewport()
                assert slot_data(self.sub.get_widget_slot(widget))==slot_data(original_slot)
                self.result['fixture_actions'].append({'id':entry['id'],'widget':ref(widget),'kind':key,
                    'action':'existing RemoveFromParent -> existing AddToPlayerScreen(0) -> restore exact saved viewport slot',
                    'same_widget':True,'added':added,'owning_controller':ref(entry['pc'])})
        self.result['immediate_after']=self.snapshot()
        self.result['status']='waiting_for_callbacks';self.poll_started=time.monotonic();self.deadline=self.poll_started+5.0
        self.write();_ACTIVE_HUD_REATTACH.add(self)
        self.handle=ue.register_slate_post_tick_callback(self.tick)

    def widget_snapshot(self,w,key):
        names=('DisplayedFlares','DisplayedDead','ShowSixHUD','DisplayRoundName','DisplayObjective','DisplayTools','DisplaySpectator','DisplayTeam') if key=='hud' else ('ShowPrompt','ShowProgress','Progress','Prompt')
        data={}
        for name in names:
            value=w.get_editor_property(name);data[name]=str(value) if name=='Prompt' else value
        return {'path':ref(w),'controller':ref(w.get_owning_player()),'world':ref(w.get_world()),
            'is_in_viewport':w.is_in_viewport(),'subsystem_widget_added':self.sub.is_widget_added(w),
            'slot':slot_data(self.sub.get_widget_slot(w)),
            'visibility':str(w.get_visibility()),'opacity':float(w.get_render_opacity()),
            'data':data,'cache':bounds(w.get_cached_geometry()),'paint':bounds(w.get_paint_space_geometry()),'tick':bounds(w.get_tick_space_geometry())}

    def snapshot(self):
        rows=[]
        active=list(w for w in ue.ObjectIterator(ue.UserWidget) if w.is_in_viewport())
        unique=True
        for e in self.entries:
            p=e['pawn'];pc=e['pc'];hud=e['hud'];prompt=e['prompt']
            for w in (hud,prompt):
                unique=unique and len([a for a in active if a.get_class()==w.get_class() and a.get_owning_player()==pc])==1
            rows.append({'id':e['id'],'host':p.get_world()==self.server,'primary':pc.is_primary_player(),'controller':ref(pc),
                'stock':int(p.get_component_by_class(self.tools).get_editor_property('FlaresLeft')),
                'dead':bool(p.get_component_by_class(self.health).call_method('IsDead')),
                'pixels':vec(ue.WidgetLayoutLibrary.get_viewport_size(pc)),
                'viewport':bounds(ue.WidgetLayoutLibrary.get_viewport_widget_geometry(pc)),
                'player':bounds(ue.WidgetLayoutLibrary.get_player_screen_widget_geometry(pc)),
                'hud':self.widget_snapshot(hud,'hud'),'prompt':self.widget_snapshot(prompt,'prompt')})
        return {'owners':rows,'unique_active_widgets':bool(unique)}

    def assess(self,snapshot):
        before={o['id']:o for o in self.result['before']['owners']}
        ownership=bool(snapshot['unique_active_widgets']);data=True;layout=True;paint=True;viewport=True;cache_tick=True
        for o in snapshot['owners']:
            b=before[o['id']];ownership=ownership and o['controller']==b['controller']
            data=data and o['stock']==b['stock'] and o['dead']==b['dead']
            viewport=viewport and positive(o['viewport']) and positive(o['player'])
            for key in ('hud','prompt'):
                w=o[key];old=b[key]
                ownership=ownership and w['path']==old['path'] and w['controller']==old['controller'] and w['world']==old['world'] and w['is_in_viewport'] and w['subsystem_widget_added']
                data=data and w['data']==old['data']
                layout=layout and w['slot']==old['slot'] and w['visibility']==old['visibility'] and w['opacity']==old['opacity']
                paint=paint and positive(w['paint'])
                cache_tick=cache_tick and positive(w['cache']) and positive(w['tick'])
        return {'owner_and_widget_identity_preserved':bool(ownership),'owner_data_preserved':bool(data),'original_slots_and_style_preserved':bool(layout),
            'nonzero_widget_paint_proof':bool(paint),'nonzero_viewport_and_player_bounds':bool(viewport),'nonzero_cache_and_tick_bounds':bool(cache_tick),
            'geometry_qualified':bool(paint and viewport and cache_tick)}

    def tick(self,delta):
        if self.finished:return
        try:
            self.callbacks+=1
            if time.monotonic()>=self.deadline:
                sample=self.result.get('last_after',self.result['immediate_after'])
                self.result['last_after']=sample;self.result['checks']=self.assess(sample)
                self.finish('wall_deadline');return
            sample=self.snapshot();checks=self.assess(sample)
            self.result['samples'].append({'callback':self.callbacks,'wall_seconds':round(time.monotonic()-self.poll_started,6),'snapshot':sample,'checks':checks})
            self.result['last_after']=sample;self.result['checks']=checks
            if self.callbacks>=8 or time.monotonic()>=self.deadline:
                self.finish('callback_limit' if self.callbacks>=8 else 'wall_deadline')
        except Exception:self.finish('callback_error',traceback.format_exc())

    def finish(self,reason,error=None):
        if self.finished:return
        self.finished=True
        if self.handle is not None:ue.unregister_slate_post_tick_callback(self.handle);self.handle=None
        _ACTIVE_HUD_REATTACH.discard(self)
        checks=self.result.get('checks',{})
        qualified=bool(checks.get('geometry_qualified'))
        self.result['geometry_qualified']=qualified;self.result['nonzero_widget_paint_proof']=bool(checks.get('nonzero_widget_paint_proof'))
        self.result['passed']=bool(not error and qualified and checks.get('owner_and_widget_identity_preserved') and checks.get('owner_data_preserved') and checks.get('original_slots_and_style_preserved'))
        self.result['status']='reattachment_geometry_qualified' if self.result['passed'] else 'reattachment_still_unqualified'
        self.result['stop_reason']=reason;self.result['actual_callbacks']=self.callbacks
        self.result['elapsed_seconds']=round(time.monotonic()-self.started,6)
        if error:self.result['error']=error
        self.write()

    def write(self):
        OUT.parent.mkdir(parents=True,exist_ok=True)
        temp=OUT.with_suffix('.json.tmp');temp.write_text(json.dumps(self.result,indent=2));temp.replace(OUT)


probe=None
try:
    probe=ReattachmentProbe()
    probe.reattach()
except Exception:
    error=traceback.format_exc()
    if probe is not None:
        cleanup_errors=[]
        for entry in probe.entries:
            for key in ('hud','prompt'):
                try:
                    widget=entry[key]
                    if not widget.is_in_viewport():
                        assert widget.add_to_player_screen(0),'Existing widget restoration failed'
                    probe.sub.set_widget_slot(widget,entry[key+'_slot'])
                except Exception:cleanup_errors.append({'widget':ref(entry[key]),'error':traceback.format_exc()})
        probe.result['cleanup_errors']=cleanup_errors
        probe.finish('reattach_error',error)
    report={'schema':1,'status':'preflight_or_reattach_error','passed':False,'pie_only':True,
        'geometry_qualified':False,'nonzero_widget_paint_proof':False,'race_claim':False,
        'rendered_pixel_acceptance':False,'native_log_scan_pending':True,'error':error,
        'script_file':str(SOURCE),'script_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
    if OUT.exists():
        report=json.loads(OUT.read_text())
        if probe is None:report.update({'status':'preflight_or_reattach_error','passed':False,'error':error})
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2))
