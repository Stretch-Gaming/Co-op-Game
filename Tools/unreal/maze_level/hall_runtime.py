"""Owning-input two-hall gate and regroup checks on genuine network PIE worlds."""
import json,time,sys,types,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
old=json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
for command in ('t.IdleWhenNotForeground 0','Slate.AllowSlateToSleep 0','Slate.bAllowThrottling 0'):
    ue.SystemLibrary.execute_console_command(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(),command)
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
G=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
V=ue.load_asset('/Game/Player/AC_PlayerView').generated_class()
lib=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
args=globals().get('ARGS',{})
cases=[tuple(c) for c in args.get('cases',[(2,'joining'),(3,'joining'),(4,'joining'),(4,'host_split')])]
assert all(c in ((2,'joining'),(3,'joining'),(4,'joining'),(4,'host_split')) for c in cases)
output=args.get('output','hall-runtime.json');assert output.endswith('.json') and Path(output).name==output
report={'passed':False,'cases':[],'method':'Legal GameMode round-chain setup fixture; actual owning F/Q and native overlap/regroup thereafter; ghosts isolated. ApplyDamage wipe fixtures check game-driven R3 retries before and after HallB. Not first-room or full traversal acceptance.'}
state={'case':0,'phase':'closed','at':time.monotonic(),'deadline':time.monotonic()+500}
def step(phase):state['phase']=phase;state['at']=time.monotonic()
def sub(p):return lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(p.get_controller(),ue.EnhancedInputLocalPlayerSubsystem.static_class()))
def inject(p,name,value):
    folder='/Game/Input/Actions/' if name in ('IA_Move','IA_Jump') else '/Game/Core/Input/'
    sub(p).inject_input_vector_for_action(ue.load_asset(folder+name),value if isinstance(value,ue.Vector) else ue.Vector(value,0,0),[],[])
def finish_case(passed,error=None):
    if state.get('rt'):
        if not passed:
            try:state['observations'].append({'failure_snapshot':snapshot()})
            except Exception:state['observations'].append({'snapshot_error':traceback.format_exc()})
        try:state['rt'].cleanup_input()
        except Exception:passed=False;error=(error or '')+traceback.format_exc()
    report['cases'].append({'players':cases[state['case']][0],'profile':cases[state['case']][1],
        'passed':passed,'error':error,'phase':state['phase'],'checks':state.get('checks',[]),
        'observations':state.get('observations',[]),'network':state['rt'].world_inventory if state.get('rt') else []})
    (QUEUE/(output.removesuffix('.json')+'-progress.json')).write_text(json.dumps(report,indent=2))
    editor.editor_request_end_play();step('closing')
def configure():
    n,profile=cases[state['case']]
    OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_Client' if profile=='joining' else 'PIE_ListenServer',
        'PlayNumberOfClients':n if profile=='joining' else n-1,'RunUnderOneProcess':True}))
    assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
    state['rt']=None;state['checks']=[];state['observations']=[];editor.editor_request_begin_play();step('warm')
def instructions(expected):
    rt=state['rt'];rows=[{'world':w.get_path_name(),'instruction':str(ue.GameplayStatics.get_game_state(w).get_editor_property('AdventureInstruction'))} for w in rt.worlds]
    if not all(r['instruction']==expected for r in rows):return False
    state['observations'].append({'instruction_replicas':rows,'round':rt.round()});return True
def begin_retry(hall):
    rt=state['rt'];state['retry_hall']=hall;state['retry_attempt']=rt.round()['attempt'];state['retry_failed_clock']=None
    for i in range(len(rt.players)):rt.kill(i)
    step('retry')
def snapshot():
    rt=state['rt'];actors=[]
    for a in ue.GameplayStatics.get_all_actors_of_class(rt.server,ue.Actor):
        if a.get_class().get_name() not in ('BP_CrystalLock_C','BP_Flare_C'):continue
        p=a.get_actor_location();row={'actor':a.get_actor_label(),'class':a.get_class().get_name(),'position':[p.x,p.y,p.z]}
        fields=('Enabled','Lit','SourceCount','LightSources') if a.get_class().get_name()=='BP_CrystalLock_C' else ('LightTarget','BurnStarted','BurnSeconds')
        for field in fields:row[field]=str(a.get_editor_property(field))
        actors.append(row)
    owners=[]
    for i,p in enumerate(rt.players):
        loc=p.get_actor_location();tools=p.get_component_by_class(rt.TOOLS)
        owners.append({'index':i,'position':[loc.x,loc.y,loc.z],'dead':rt.dead(i),
            'base_aim':str(p.get_base_aim_rotation()),'owner_control':str(rt.local(i).get_controller().get_control_rotation()),
            'server_lamp':p.get_component_by_class(V).call_method('GetHeadlampOn'),
            'owner_lamp':rt.local(i).get_component_by_class(V).call_method('GetHeadlampOn'),
            'beam_target':str(tools.get_editor_property('BeamTarget')),'stock':tools.get_editor_property('FlaresLeft')})
    return {'round':rt.round(),'stage':rt.mode().get_editor_property('MazeHallStage'),'actors':actors,'owners':owners}
def setup_hall(letter):
    rt=state['rt'];n=len(rt.players);gm=rt.mode();state['hall']=letter
    beam_count=1 if n==2 else 2;flare_count=2 if n==4 else 1
    living=rt.alive_roster();assert len(living)>=beam_count
    if cases[state['case']][1]=='host_split':
        # Exercise the independently owning second host controller, plus a remote.
        living.sort(key=lambda i:0 if rt.local(i).get_world()==rt.server and not rt.local(i).get_controller().is_primary_player() else (1 if rt.local(i).get_world()!=rt.server else 2))
    beams=living[:beam_count];throws=[living[i%len(living)] for i in range(flare_count)]
    if cases[state['case']][1]=='host_split':assert any(rt.local(i).get_world()==rt.server and not rt.local(i).get_controller().is_primary_player() for i in beams)
    state['observations'].append({'hall':letter,'input_owners':[{'index':i,'world':rt.local(i).get_world().get_path_name(),'controller':rt.local(i).get_controller().get_path_name(),'primary_controller':rt.local(i).get_controller().is_primary_player(),'beam':i in beams,'throw':i in throws} for i in sorted(set(beams+throws))]})
    state.update(beams=beams,throws=throws)
    for bowl,i in enumerate(throws):
        a=rt.actor(('Six_braziers_' if letter=='A' else 'Maze_HallB_braziers_')+str(bowl));p=a.get_actor_location()
        rt.place(i,(p.x-90,p.y,p.z+100));rt.local(i).get_controller().set_control_rotation(ue.Rotator(pitch=-60,yaw=0))
    step('throw_approach')
def aim_beams():
    rt=state['rt'];letter=state['hall']
    for slot,i in enumerate(state['beams']):
        target=rt.actor(('Six_headlamp_locks_' if letter=='A' else 'Maze_HallB_headlamp_locks_')+str(slot))
        rt.aim(i,target)
def tick(delta):
    try:
        now=time.monotonic();assert now<state['deadline'],'Hall matrix wall deadline'
        if state['phase']=='closed':configure();return
        worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));age=now-state['at']
        if state['phase']=='closing':
            if worlds:return
            if not report['cases'][-1]['passed'] or state['case']+1==len(cases):
                report['passed']=all(c['passed'] for c in report['cases']) and len(report['cases'])==len(cases)
                (QUEUE/output).write_text(json.dumps(report,indent=2));OBJ.set_properties(settings,json.dumps(old));ue.unregister_slate_post_tick_callback(state['handle']);return
            state['case']+=1;step('closed');return
        if state['phase']=='warm':
            assert age<35,'Possessed roster timeout'
            if age<2:return
            owners=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled() and p.player_state]
            n,profile=cases[state['case']]
            if profile=='host_split' and len(owners)==n-1:
                server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));host=next(p for p in owners if p.get_world()==server)
                state['host']=host;step('add');return
            if len(owners)!=n:return
            path=ROOT/'Tools/unreal/six_round/core/tests/runtime.py';source=path.read_text()
            guard="Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')";assert source.count(guard)==1
            module=types.ModuleType('maze_hall_runtime');module.__file__=str(path)
            exec(compile(source.replace(guard,'Path('+repr(str(ROOT))+')'),str(path),'exec'),module.__dict__)
            rt=module.Runtime(n,profile);state['rt']=rt;gm=rt.mode()
            for i,g in enumerate(ue.GameplayStatics.get_all_actors_of_class(rt.server,G)):g.set_actor_location(ue.Vector(60000+i*200,60000,2000),False,True)
            for i in range(n):rt.place(i,(-900,(i-1.5)*130,100))
            gm.call_method('StartRound',args=(1,));gm.call_method('ClearRound');gm.call_method('StartRound',args=(2,));gm.call_method('ClearRound')
            assert rt.round()['index']==3 and rt.round()['phase']==1;state['checks'].append('Legal phase setup reaches HallA puzzle')
            for i in range(n):rt.place(i,(-175,9250+(i-1.5)*120,-200))
            step('start_A');return
        if state['phase']=='add':
            inject(state['host'],'IA_AddLocalPlayer',1 if age<.15 else 0)
            if age>1:step('warm')
            return
        rt=state['rt'];assert rt.ready()
        for i,g in enumerate(ue.GameplayStatics.get_all_actors_of_class(rt.server,G)):g.set_actor_location(ue.Vector(60000+i*200,60000,2000),False,True)
        gm=rt.mode();stage=gm.get_editor_property('MazeHallStage')
        if state['phase']=='start_A':
            assert age<5,'HallA instruction replication timeout'
            if not instructions('Meeting hall A: light its locks together.'):return
            if cases[state['case']]==(2,'joining'):begin_retry('A')
            else:setup_hall('A')
        elif state['phase']=='retry':
            assert age<10,('R3 retry timeout',state['retry_hall'],rt.round())
            s=rt.round()
            if s['phase']==3 and state['retry_failed_clock'] is None:
                state['retry_failed_clock']=rt.clock();state['retry_ends']=s['ends']
                assert all(rt.dead(i) for i in range(len(rt.players)))
            if state['retry_failed_clock'] is not None and rt.clock()<state['retry_ends']-.06:
                assert s['phase']==3 and s['attempt']==state['retry_attempt']
            if s['attempt']==state['retry_attempt']+1:
                assert state['retry_failed_clock'] is not None and rt.clock()>=state['retry_ends']-.06
                assert s['index']==3 and s['phase']==1
                hall=state['retry_hall'];expected_y=9250 if hall=='A' else 15500;expected_z=-200 if hall=='A' else 500
                assert stage==(0 if hall=='A' else 2)
                assert not gm.get_editor_property('MazeHallBCleared')
                assert bool(gm.get_editor_property('MazeHallBReached'))==(hall=='B')
                for i,p in enumerate(rt.players):
                    health=p.get_component_by_class(rt.H);assert not rt.dead(i) and health.get_editor_property('Health')==health.get_editor_property('MaxHealth')
                    pos=p.get_actor_location();slot=p.player_state.get_editor_property('ColorSlot')
                    assert (pos-ue.Vector(-175,expected_y+(slot-1.5)*150,expected_z)).length()<140,(hall,pos)
                    assert p.get_component_by_class(rt.TOOLS).get_editor_property('FlaresLeft')==3
                state['checks'].append('Game-driven three-second R3 wipe retry restores roster at Hall'+hall+' with one attempt increment and full stock')
                state['observations'].append({'retry_hall':hall,'round':s,'server_seconds_since_failed_observation':rt.clock()-state['retry_failed_clock']})
                setup_hall(hall)
        elif state['phase']=='throw_approach':
            assert age<6,'Throw approach/aim did not replicate before owning Q'
            ready=age>.8;rows=[]
            for bowl,i in enumerate(state['throws']):
                target=rt.actor(('Six_braziers_' if state['hall']=='A' else 'Maze_HallB_braziers_')+str(bowl));pos=target.get_actor_location()
                rt.local(i).get_controller().set_control_rotation(ue.Rotator(pitch=-60,yaw=0))
                expected=ue.Vector(pos.x-90,pos.y,pos.z+90)
                server=rt.players[i].get_actor_location();local=rt.local(i).get_actor_location()
                aim=rt.players[i].get_base_aim_rotation()
                rows.append({'owner':i,'server':str(server),'local':str(local),'base_aim':str(aim)})
                delta_aim=ue.MathLibrary.normalized_delta_rotator(aim,ue.Rotator(pitch=-60,yaw=0))
                ready=ready and (server-expected).length()<80 and (local-expected).length()<80 and abs(delta_aim.pitch)<3 and abs(delta_aim.yaw)<3
            state['last_throw_approach']=rows
            if ready:
                state['observations'].append({'throw_approach_ready':rows});step('throw')
        elif state['phase']=='throw':
            for i in state['throws']:rt.inject(i,'IA_ThrowFlare',1 if age<.2 else 0)
            if age>1:
                for slot,i in enumerate(state['beams']):
                    target=rt.actor(('Six_headlamp_locks_' if state['hall']=='A' else 'Maze_HallB_headlamp_locks_')+str(slot));p=target.get_actor_location()
                    rt.place(i,(p.x,p.y-150,p.z+45));rt.aim(i,target)
                    if not rt.local(i).get_component_by_class(V).call_method('GetHeadlampOn'):rt.inject(i,'IA_Headlamp',1);rt.inject(i,'IA_Headlamp',0)
                state['sampled']=set()
                step('light')
        elif state['phase']=='light':
            for mark in (1,3,6):
                if age>mark and mark not in state['sampled']:
                    state['sampled'].add(mark);state['observations'].append({'phase_seconds':age,'snapshot':snapshot()})
            aim_beams();assert age<12,('Hall did not clear via owning inputs',state['hall'],stage)
            if state['hall']=='A' and stage==1:
                assert rt.round()['index']==3 and gm.get_editor_property('MazeHallACleared') and not gm.get_editor_property('MazeHallBCleared')
                if not all(rt.actor('Maze_Hall0_Door_'+str(i)).get_editor_property('Open') for i in range(4)):return
                assert not any(rt.actor('Maze_Hall1_Door_'+str(i)).get_editor_property('Open') for i in range(4))
                if not instructions('The way is open: follow the maze to meeting hall B.'):return
                state['checks'].append('HallA owning lamp/flare unlocks only middle paths; Round4 remains blocked')
                rt.kill(0);state['victim']=0
                living=rt.alive_roster();state['last_arriver']=living[-1]
                for i in living:
                    if i!=state['last_arriver']:rt.place(i,(-175,15500+(i-1.5)*100,500))
                    else:rt.place(i,(-175,9250,-200))
                step('partial_B')
            elif state['hall']=='B' and rt.round()['index']==4:
                assert gm.get_editor_property('MazeHallBCleared') and gm.get_editor_property('MazeHallBReached')
                if not all(rt.actor('Maze_Hall1_Door_'+str(i)).get_editor_property('Open') for i in range(4)):return
                if not instructions('Follow the deep maze to the relic chamber.'):return
                state['checks'].append('HallB owning lamp/flare unlocks final paths and enters Round4')
                finish_case(True)
        elif state['phase']=='partial_B':
            assert rt.round()['index']==3 and stage==1 and rt.dead(state['victim']) and not gm.get_editor_property('MazeHallBReached')
            if age>.8:
                state['checks'].append('HallB partial living roster cannot trigger regroup or advance the round')
                for i in rt.alive_roster():rt.place(i,(-175,15500+(i-1.5)*100,500))
                step('arrive_B')
        elif state['phase']=='arrive_B':
            assert age<8,'HallB arrival/regroup timeout'
            if stage==2:
                assert not rt.dead(state['victim']);p=rt.players[state['victim']].get_actor_location()
                assert abs(p.y-15500)<500 and abs(p.z-500)<20,('HallB revival returned to wrong hall',p)
                assert all(p.get_component_by_class(rt.TOOLS).get_editor_property('FlaresLeft')==(3 if len(rt.players)==2 else 2) for p in rt.players)
                if not instructions('Meeting hall B: light its locks together.'):return
                state['checks'].append('All-living HallB arrival revives at HallB and restocks every owner')
                if cases[state['case']]==(2,'joining'):begin_retry('B')
                else:setup_hall('B')
    except Exception:finish_case(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':output,'cases':cases,'gameplay_input':'owning Enhanced Input F/Q; disclosed round and approach fixtures'}
