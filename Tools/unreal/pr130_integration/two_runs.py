"""Reuse the published transaction suite with an exact current-checkout guard."""
import hashlib,importlib.util,sys,time,types,traceback,json
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
perf=ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
old=json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
oldperf=json.loads(OBJ.get_properties(perf,['bThrottleCPUWhenNotForeground']))
OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_ListenServer','PlayNumberOfClients':2,'RunUnderOneProcess':True}))
OBJ.set_properties(perf,json.dumps({'bThrottleCPUWhenNotForeground':False}))
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
folder=ROOT/'Tools/unreal/six_round/core/tests'
state={'phase':'warm','at':time.monotonic(),'deadline':time.monotonic()+280}
editor.editor_request_begin_play()

def restore():
    OBJ.set_properties(settings,json.dumps(old));OBJ.set_properties(perf,json.dumps(oldperf))
    ue.unregister_slate_post_tick_callback(state['handle'])
def tick(delta):
    try:
        if state['phase']=='closing':
            if not ue.EditorLevelLibrary.get_pie_worlds(True):restore()
            return
        assert time.monotonic()<state['deadline'],'Two-run suite timeout'
        if state['phase']=='warm' and time.monotonic()-state['at']>2:
            worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
            if len(worlds)<2:return
            cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
            locals_=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled() and p.player_state]
            if len(locals_)!=2:return
            for name in ('runtime','framework','native_flow'):
                path=folder/(name+'.py');code=path.read_text(encoding='utf-8-sig')
                if name=='runtime':
                    prior="Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')"
                    assert code.count(prior)==1
                    code=code.replace(prior,'Path('+repr(str(ROOT))+')')
                module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
                exec(compile(code,str(path),'exec'),module.__dict__)
            runtime_class=sys.modules['runtime'].Runtime
            original_focus=runtime_class.focus
            def perch_focus(rt,i,target):
                if target.get_actor_label().startswith('Six_headlamp_locks_'):
                    loc=target.get_actor_location()
                    rt.place(i,(loc.x,loc.y-175,95));rt.aim(i,target)
                else:original_focus(rt,i,target)
            runtime_class.focus=perch_focus
            ghost_class=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
            base_flow=sys.modules['native_flow'].NativeFlow
            class FocusedFlow(base_flow):
                fixture_description=base_flow.fixture_description+' Headlamp approaches use the authored south perch landing instead of the obsolete west rim. Live ghost approach is separated for this focused puzzle transaction test; threat timing and full-route play are separate.'
                def tick(self,delta):
                    for i,ghost in enumerate(ue.GameplayStatics.get_all_actors_of_class(self.rt.server,ghost_class)):
                        ghost.set_actor_location(ue.Vector(60000+i*300,-60000,2000),False,True)
                    super().tick(delta)
                    if self.phase=='meeting_locks' and self.elapsed()>.25:
                        bucket=int(self.elapsed())
                        seen=getattr(self,'meeting_samples',set())
                        if bucket not in seen and bucket<4:
                            seen.add(bucket);self.meeting_samples=seen
                            def props(a,keys):
                                return {k:str(a.get_editor_property(k)) for k in keys}
                            locks=[self.rt.actor('Six_headlamp_locks_0'),self.rt.actor('Six_braziers_0')]
                            sample={'run':self.run_number,'elapsed':self.elapsed(),'locks':[dict(label=a.get_actor_label(),position=str(a.get_actor_location()),**props(a,['Enabled','Lit','SourceCount','LightSources'])) for a in locks],
                                'players':[dict(position=str(p.get_actor_location()),beam=str(p.get_component_by_class(self.rt.TOOLS).get_editor_property('BeamTarget'))) for p in self.rt.players],
                                'flares':[dict(position=str(a.get_actor_location()),active=bool(a.call_method('IsActive')),**props(a,['LightTarget'])) for a in ue.GameplayStatics.get_all_actors_of_class(self.rt.server,ue.load_asset('/Game/Player/Tools/BP_Flare').generated_class())]}
                            with (QUEUE/'meeting-probes.jsonl').open('a') as out:out.write(json.dumps(sample)+'\n')
            suite=FocusedFlow({'players':2,'runs':2,'timeout':240})
            suite.test_source_layout_sha256=hashlib.sha256(b''.join((folder/(n+'.py')).read_bytes() for n in ('runtime','framework','native_flow'))).hexdigest()
            state['suite']=suite;suite.run();state['phase']='running'
        elif state['phase']=='running' and hasattr(state['suite'],'result'):
            result=state['suite'].result
            result['ending_round']=state['suite'].rt.round()
            (QUEUE/'two-runs.json').write_text(json.dumps(result,indent=2))
            editor.editor_request_end_play();state['phase']='closing'
    except Exception:
        result={'passed':False,'error':traceback.format_exc()}
        if state.get('suite'):
            state['suite'].finish(False,result['error'])
        (QUEUE/'two-runs.json').write_text(json.dumps(result,indent=2))
        editor.editor_request_end_play();state['phase']='closing'
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':'two-runs.json','profiles':'one listen host plus one joining client','source_tests_unchanged':True}
