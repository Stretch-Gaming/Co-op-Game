"""Native owning-input gap/recovery and continuous heavy-carrier route checks.

Each obstacle has one disclosed server approach fixture. Return has one initial
key approach, then no pawn position setters until completion/results.
"""
import json,time,types,traceback,math,sys
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
from pathlib import Path
sys.path.insert(0,str(HERE))
from layout import Floors
import gzip
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
old=json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_ListenServer','PlayNumberOfClients':2,'RunUnderOneProcess':True}))
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
layout=json.loads((QUEUE/'layout.json').read_text());floors=Floors(json.loads(gzip.decompress((ROOT/layout['source']).read_bytes())))
report={'passed':False,'checks':[],'obstacles':[],'fixtures':['Single server approach before each obstacle; ghosts isolated','Legal GameMode phase-chain setup to R5; single lever/key approach then continuous owning movement through R6'],'physical_keyboard_tested':False}
state={'phase':'warm','at':time.monotonic(),'deadline':time.monotonic()+720,'case':int(ARGS.get('start_case',0))}
editor.editor_request_begin_play()
def step(p):state['phase']=p;state['at']=time.monotonic()
def point(g,along,across=0,z=None):
    c,f=g['center'],g['forward'];p=[c[0]+f[0]*along-f[1]*across,c[1]+f[1]*along+f[0]*across,0]
    p[2]=floors.at(g['source_floor'],p[0],p[1])+96 if z is None else z
    return p
def move(i,target,speed=1):
    rt=state['rt'];p=rt.players[i].get_actor_location();v=ue.Vector(*target)-p;d=math.hypot(v.x,v.y)
    rt.local(i).get_controller().set_control_rotation(ue.Rotator(yaw=math.degrees(math.atan2(v.y,v.x))))
    rt.inject(i,'IA_Move',ue.Vector(0,speed if d>18 else 0,0));return d
def along(g,p):return (p.x-g['center'][0])*g['forward'][0]+(p.y-g['center'][1])*g['forward'][1]
def start_gap():
    rt=state['rt'];g=layout['gaps'][state['case']//2];miss=state['case']%2==1
    state.update(gap=g,miss=miss,airborne=False,min_z=1e9,max_z=-1e9)
    rt.place(0,point(g,-g['length']/2-(350 if g['length']>250 else 130)))
    rt.inject(0,'IA_Sprint',0);rt.inject(0,'IA_Jump',0);step('settle_gap')
def prepare_key():
    gm=state['rt'].mode()
    gm.call_method('StartRound',args=(1,));gm.call_method('ClearRound');gm.call_method('StartRound',args=(2,));gm.call_method('ClearRound')
    lib=ue.load_object(None,'/Script/Engine.Default__KismetSystemLibrary')
    for name in ('MazeHallACleared','MazeHallBReached','MazeHallBCleared'):lib.call_method('SetBoolPropertyByName',args=(gm,name,True))
    lib.call_method('SetIntPropertyByName',args=(gm,'MazeHallStage',3));gm.call_method('ClearRound')
    report['fixtures'].append('R5 preparation bypasses separately tested HallB puzzle using MazeHallBCleared fixture before GameMode clear; not full-run proof')
    step('key_stage')
def finish(ok,error=None):
    report.update(passed=ok,error=error,phase=state['phase'])
    if state.get('rt'):
        p=state['rt'].players[0].get_actor_location()
        nodes=state.get('recovery_nodes',[]);index=state.get('recovery_index',0)
        report['last_sample']={'case':state['case'],'position':[p.x,p.y,p.z],'min_z':state.get('min_z'),'max_z':state.get('max_z'),'airborne':state.get('airborne'),'recovery_index':index,'target':nodes[index] if index<len(nodes) else None}
        report['last_sample'].update(round=state['rt'].round(),can_input=state['rt'].players[0].call_method('CanAcceptSixInput'),max_step=state['rt'].players[0].character_movement.max_step_height)
        report['owners']=[{'position':str(p.get_actor_location()),'focused':str(state['rt'].local(i).get_editor_property('FocusedTarget'))} for i,p in enumerate(state['rt'].players)]
        target=report['last_sample']['target']
        if target:
            end=ue.Vector(target[0],target[1],p.z)
            hit=ue.SystemLibrary.capsule_trace_single(state['rt'].server,p,end,42,96,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[state['rt'].players[0]],ue.DrawDebugTrace.NONE,True)
            if hit:
                d=hit.to_dict();a=d.get('hit_actor');report['last_sample']['blocked_by']={'actor':a.get_actor_label() if a else None,'point':str(d.get('impact_point')),'normal':str(d.get('impact_normal'))}
    if state.get('rt'):
        try:state['rt'].cleanup_input();state['rt'].inject(0,'IA_Jump',0)
        except Exception:report.update(passed=False,cleanup_error=traceback.format_exc())
    (QUEUE/'traversal-runtime.json').write_text(json.dumps(report,indent=2));editor.editor_request_end_play();step('closing')
def tick(delta):
    try:
        age=time.monotonic()-state['at'];worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
        if state['phase']=='closing':
            if not worlds:OBJ.set_properties(settings,json.dumps(old));ue.unregister_slate_post_tick_callback(state['handle'])
            return
        assert time.monotonic()<state['deadline'],'Traversal suite deadline'
        if state['phase']=='warm':
            assert age<35
            if age<2:return
            path=ROOT/'Tools/unreal/six_round/core/tests/runtime.py';source=path.read_text();guard="Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')"
            m=types.ModuleType('maze_traversal_runtime');m.__file__=str(path)
            exec(compile(source.replace(guard,'Path('+repr(str(ROOT))+')'),str(path),'exec'),m.__dict__)
            try:rt=m.Runtime(2)
            except AssertionError:return
            state['rt']=rt;report['network']=rt.world_inventory
            if state['case']<8:start_gap()
            else:prepare_key()
            return
        rt=state['rt']
        if not rt.ready():
            assert age<20,'Network roster did not recover after travel'
            return
        ghost=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
        for g in ue.GameplayStatics.get_all_actors_of_class(rt.server,ghost):g.set_actor_location(ue.Vector(60000,60000,2000),False,True)
        owner=state.get('carrier',0)
        assert not rt.dead(owner),'Traversal owner died'
        if state['phase']=='settle_gap':
            if age>1:step('gap')
        elif state['phase']=='gap':
            assert age<10,('Gap did not cross',state['case'],str(rt.players[0].get_actor_location()))
            g=state['gap'];p=rt.players[0].get_actor_location();a=along(g,p);state['min_z']=min(state['min_z'],p.z);state['max_z']=max(state['max_z'],p.z)
            rt.inject(0,'IA_Sprint',1 if g['length']>250 and not state['miss'] else 0)
            move(0,point(g,g['length']/2+90))
            jumping=not state['miss'] and -g['length']/2-50<a<-g['length']/2+5
            rt.inject(0,'IA_Jump',1 if jumping else 0)
            state['airborne']=state['airborne'] or rt.players[0].character_movement.is_falling()
            if state['miss'] and p.z<g['center'][2]-90:
                rt.inject(0,'IA_Move',0);f=g['forward'];state['recovery_nodes']=[point(g,g['length']/2-70,125,g['pit_floor']+96)]+[[q['location'][0]+f[1]*25,q['location'][1]-f[0]*25,q['location'][2]+q['size'][2]/2+96] for q in g['primitives'] if 'MazeLevel.Recovery' in q.get('tags',[])]+[point(g,g['length']/2+660,125)]
                state['recovery_index']=0;step('recover')
            elif not state['miss'] and a>g['length']/2+60 and not rt.players[0].character_movement.is_falling():
                assert state['airborne'] and state['min_z']>g['center'][2]-40,(g['id'],state['airborne'],state['min_z'],g['center'],str(p))
                report['obstacles'].append({'id':g['id'],'test':'owning sprint/jump' if g['length']>250 else 'owning walking jump','passed':True,'min_z':state['min_z'],'max_z':state['max_z']});rt.inject(0,'IA_Jump',0);rt.inject(0,'IA_Sprint',0);state['case']+=1;start_gap()
        elif state['phase']=='recover':
            assert age<18,('Recovery stuck',state['case'],str(rt.players[0].get_actor_location()))
            index=state['recovery_index'];target=state['recovery_nodes'][index]
            if move(0,target,.65)<35:
                state['recovery_index']+=1
                if state['recovery_index']==len(state['recovery_nodes']):
                    p=rt.players[0].get_actor_location();g=state['gap'];assert p.z>g['recovery']['exit'][2]+60 and not rt.dead(0)
                    report['obstacles'].append({'id':g['id'],'test':'deliberate missed jump; owning walk up same-path stairs','passed':True,'exit':str(p)});state['case']+=1
                    if state['case']<8:start_gap()
                    else:
                        rt.inject(0,'IA_Move',0);prepare_key()
        elif state['phase']=='key_stage':
            assert age<8,('R5 setup timeout',rt.round())
            if rt.round()['index']==4 and rt.round()['phase']==1:rt.mode().call_method('ClearRound')
            if rt.round()['index']==5 and rt.round()['phase']==1:
                for i,target in ((1,rt.actor('Six_RelicLever_0')),(0,rt.key())):
                    loc=target.get_actor_location();rt.place(i,(loc.x,loc.y-180,loc.z+100));rt.aim(i,target)
                step('key_approach')
        elif state['phase']=='key_approach':
            assert age<6
            rt.aim(1,rt.actor('Six_RelicLever_0'));rt.aim(0,rt.key())
            if age>1 and rt.focused(1,rt.actor('Six_RelicLever_0')):step('key_pickup')
        elif state['phase']=='key_pickup':
            assert age<8
            rt.aim(1,rt.actor('Six_RelicLever_0'));rt.aim(0,rt.key())
            rt.inject(1,'IA_Interact',1);rt.inject(0,'IA_Interact',1 if age>1 and rt.focused(0,rt.key()) else 0)
            if rt.round()['index']==6:
                assert rt.carried(0)==rt.key();rt.inject(0,'IA_Interact',0);rt.inject(1,'IA_Interact',0);state['node']=0;state['walk_start']=rt.players[0].get_actor_location();state['walk_time']=rt.clock();state['trail']=[];state['last_progress']=time.monotonic();step('return')
                if ARGS.get('delivery_only'):
                    rt.kill(0);state['carrier']=1;report['fixtures'].append('Separate drop/re-pick/delivery gate uses one native approach to dropped key and starting-room altar; continuous walk is retained in separate carrier receipt');step('carrier_drop')
        elif state['phase']=='carrier_drop':
            assert age<6
            if age>.8:
                assert rt.dead(0) and rt.carried(0) is None and rt.key().get_editor_property('CarryState')==0
                loc=rt.key().get_actor_location();rt.place(1,(loc.x,loc.y-180,loc.z+100));step('re_pick')
        elif state['phase']=='re_pick':
            assert age<8
            rt.aim(1,rt.key());rt.inject(1,'IA_Interact',1 if age>.8 and rt.focused(1,rt.key()) else 0)
            if rt.carried(1)==rt.key():
                rt.inject(1,'IA_Interact',0);report['checks'].append('Carrier lethal damage drops the key; living joining teammate re-picks using owning E')
                rt.focus(1,rt.actor('Six_DropoffAltar'));step('altar')
        elif state['phase']=='return':
            assert rt.carried(0)==rt.key() and rt.round()['index']==6 and rt.round()['phase']==1
            target=layout['return_route']['nodes'][state['node']];distance=move(0,target)
            if distance<state.get('last_distance',1e9)-10:
                state['last_distance']=distance;state['last_progress']=time.monotonic()
            if not state['trail'] or rt.clock()-state['trail'][-1][0]>.5:
                p=rt.players[0].get_actor_location();state['trail'].append([rt.clock(),p.x,p.y,p.z])
            assert time.monotonic()-state['last_progress']<12,('Carrier stuck',state['node'],target,str(rt.players[0].get_actor_location()))
            if distance<55:
                state['node']+=1;state['last_progress']=time.monotonic();state['last_distance']=1e9
                if state['node']==len(layout['return_route']['nodes']):
                    rt.inject(0,'IA_Move',0);report['carrier']={'passed':True,'nodes':state['node'],'seconds':rt.clock()-state['walk_time'],'trail':state['trail'],'position_setters_during_return':0};rt.aim(0,rt.actor('Six_DropoffAltar'));step('altar')
        elif state['phase']=='altar':
            assert age<10
            rt.aim(owner,rt.actor('Six_DropoffAltar'))
            if age>1 and rt.focused(owner,rt.actor('Six_DropoffAltar')):rt.inject(owner,'IA_Interact',1)
            if rt.round()['phase']==4:
                assert rt.gs.get_editor_property('RelicsCollected')==1;rt.inject(owner,'IA_Interact',0);report['checks'].append('Owning E at original starting-room altar counts delivery once');step('results')
        elif state['phase']=='results':
            assert age<15
            if rt.map()=='L_Site02':
                report['checks'].append('Both owners travel to results after delivery');state['host']=next(i for i in range(2) if rt.local(i).get_world()==rt.server);step('restart')
        elif state['phase']=='restart':
            assert age<15;rt.inject(state['host'],'IA_RunRestart',1)
            if rt.map()=='L_SixRound_Test' and rt.round()['index']==0:
                report['checks'].append('Owning host R restarts both owners in normal starting-room lobby');finish(True)
    except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':True,'report':str(QUEUE/'traversal-runtime.json')}
