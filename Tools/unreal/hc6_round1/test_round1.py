"""Real in-process network fixture tests, driven by each owning Enhanced Input subsystem.

Server teleports only establish test approach positions. Crossings/departures use
client movement. Weight/tag changes and the explicit reset dispatch are server
fixture operations; they do not test carrying or global recovery.
"""
import sys,time,traceback,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
CONFIG=json.loads((OUT/'run-config.json').read_text())
N=CONFIG['players']
I='Index_11_91104438409472A6DD374BADC8DC29B1'
P='Phase_15_0B3D934F45B47D0BD2F25CA01264D4DF'
A='Attempt_12_246832B34F4E147660E8729696BDD44A'
R='ScalingRow_14_43C74C304230A92B6620E1A520A230C0'
worlds=list(unreal.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if unreal.GameplayStatics.get_game_state(w).has_authority())
if CONFIG.get('split'):
    # Supported local-player creation on the host; no controller index lookup.
    unreal.GameplayStatics.create_player(server,-1,True)
worlds=list(unreal.EditorLevelLibrary.get_pie_worlds(True))
gs=unreal.GameplayStatics.get_game_state(server)
gm=unreal.GameplayStatics.get_game_mode(server)
action=unreal.load_asset('/Game/Input/Actions/IA_Move')
library=unreal.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
def actors(world,cls):return list(unreal.GameplayStatics.get_all_actors_of_class(world,cls))
def by_class(world,name):return actors(world,unreal.load_class(None,'/Game/Puzzles/'+name+'.'+name+'_C'))
def prop(a,n):return a.get_editor_property(n)
def player_id(a):return prop(prop(a,'player_state'),'player_id')
def round_state(world):
    s=prop(unreal.GameplayStatics.get_game_state(world),'RoundState')
    phase=s.get_editor_property(P)
    try:phase=int(phase)
    except Exception:phase=int(re.search(r':\s*(\d+)>',str(phase))[1])
    return {'index':s.get_editor_property(I),'phase':phase,'attempt':s.get_editor_property(A),'row':str(s.get_editor_property(R))}
def phase_is(world,phase):
    actual=round_state(world)['phase']
    return actual==phase or str(actual).endswith('NewEnumerator'+str(phase))
def component_named(a,name):return next(c for c in a.get_components_by_class(unreal.SceneComponent) if c.get_name()==name)
def plate(world,slot):return next(a for a in by_class(world,'BP_PressurePlate') if prop(a,'PlateSlot')==slot)
def gate(world,index):return next(a for a in by_class(world,'BP_ChamberGate') if prop(a,'RoundIndex')==index)
def setup(world):return by_class(world,'BP_PuzzleSetup')[0]
def pad(world):return by_class(world,'BP_StartPad')[0]
def weights():return list(prop(setup(server),'Statues'))
def vec(v):return [round(v.x,3),round(v.y,3),round(v.z,3)]
def snapshot():
    result=[]
    for w in worlds:
        item={'world':w.get_path_name(),'authority':unreal.GameplayStatics.get_game_state(w).has_authority(),'round':round_state(w),
          'setup':{n:prop(setup(w),n) for n in ('Ready','PlateCount','StatueCount','BoundState')},
          'pad':{n:prop(pad(w),n) for n in ('Started','InsideCount','ExpectedCount','HoldStarted','BoundState')},'plates':[],'gates':[]}
        for a in sorted(by_class(w,'BP_PressurePlate'),key=lambda a:prop(a,'PlateSlot')):
            top=component_named(a,'PlateTop')
            item['plates'].append({'slot':prop(a,'PlateSlot'),'pressed':prop(a,'Pressed'),'enabled':prop(a,'Enabled'),
             'occupants':prop(a,'OccupantCount'),'top_z':top.get_editor_property('relative_location').z,
             'material':top.get_material(0).get_path_name() if top.get_material(0) else None})
        for a in by_class(w,'BP_ChamberGate'):
            item['gates'].append({'index':prop(a,'RoundIndex'),'open':prop(a,'Open'),
             'leaf_z':component_named(a,'GateLeaf').get_editor_property('relative_location').z})
        item['pawns']=[{'id':player_id(p),'location':vec(p.get_actor_location())} for p in actors(w,unreal.Pawn) if prop(p,'player_state')]
        result.append(item)
    return result
state={'step':-1,'started':0,'checks':[],'inputs':[],'pawns':[],'old_weights':[],'finished':False,'wall_start':time.monotonic()}
result={'config':CONFIG,'project':str(ROOT),'engine':unreal.SystemLibrary.get_engine_version(),'fixture_only':True,
 'network_input':'Enhanced Input injection per owning local player; normal Character movement replication',
 'reset_scope':'Explicit actor-interface dispatch; global recovery not tested','checks':state['checks']}
def check(ok,message):
    if not ok:raise AssertionError(message)
def write_result():
    (OUT/(CONFIG['run']+'.json')).write_text(json.dumps(result,separators=(',',':'),default=str)+'\n')
def initialize():
    pawns=sorted([p for p in actors(server,unreal.Pawn) if prop(p,'player_state')],key=player_id)
    check(len(pawns)==N,f'Expected {N} connected pawns; found {len(pawns)}')
    inputs=[]
    for pc in unreal.ObjectIterator(unreal.PlayerController):
        if pc.get_world() in worlds and pc.is_local_controller() and pc.get_controlled_pawn() and prop(pc,'player_state'):
            subsystem=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(pc,unreal.EnhancedInputLocalPlayerSubsystem.static_class()))
            check(bool(subsystem),'Missing owning input subsystem')
            inputs.append((subsystem,pc))
            pc.set_control_rotation(unreal.Rotator())
    inputs.sort(key=lambda pair:player_id(pair[1]))
    check(len(inputs)==N,f'Expected {N} local drivers; found {len(inputs)}')
    check([player_id(p) for p in pawns]==[player_id(pc) for _,pc in inputs],'Input-to-server pawn identity mismatch')
    state['pawns']=pawns;state['inputs']=inputs
    result['input_owners']=[{'player_id':player_id(pc),'controller':pc.get_path_name(),'subsystem':s.get_path_name(),'local_player':s.get_outer().get_path_name()} for s,pc in inputs]
    if CONFIG.get('split'):
        local= [pc for _,pc in inputs if pc.get_world()==server]
        check(len(local)==2,'Host does not have two owning local controllers')
        result['host_local_players']=len(local)
    check(all(prop(a,'BoundState') for w in worlds for name in ('BP_StartPad','BP_PuzzleSetup','BP_ChamberGate') for a in by_class(w,name)),'Missed GameState binding')
    check(phase_is(server,0),'Fixture must start in Lobby')
    place_pad_approaches()
def place_pad_approaches():
    for i,p in enumerate(state['pawns']):p.set_actor_location(unreal.Vector(-650,(i-(N-1)/2)*100,92.15),False,True)
def stop_input():
    for s,pc in state['inputs']:s.inject_input_vector_for_action(action,unreal.Vector(),[],[])
def move_to(targets,speed=.3):
    for i,(s,pc) in enumerate(state['inputs']):
        target=targets.get(i)
        value=0
        if target is not None:
            x=pc.get_controlled_pawn().get_actor_location().x
            if abs(x-target)>20:value=speed if x<target else -speed
        s.inject_input_vector_for_action(action,unreal.Vector(0,value,0),[],[])
def verify_pad_present():
    check(prop(pad(server),'InsideCount')==N,'Not every player entered the pad')
    check(prop(pad(server),'HoldStarted')>=0,'All-player hold did not start')
    check(phase_is(server,0) and not prop(gate(server,0),'Open'),'Pad opened before three seconds')
def verify_departure():
    check(prop(pad(server),'InsideCount')==N-1,'Departure did not remove the player')
    check(prop(pad(server),'HoldStarted')<0,'Departure did not cancel the hold')
    check(phase_is(server,0) and not prop(gate(server,0),'Open'),'Incomplete pad opened the entrance')
def add_fixture_participant():
    state['old_hold']=prop(pad(server),'HoldStarted')
    cls=unreal.load_class(None,'/Game/Core/BP_CoopPlayerState.BP_CoopPlayerState_C')
    lib=unreal.load_object(None,'/Script/Engine.Default__GameplayStatics')
    a=lib.call_method('BeginDeferredActorSpawnFromClass',args=(server,cls,unreal.Transform(),unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
    state['fixture_participant']=lib.call_method('FinishSpawningActor',args=(a,unreal.Transform(),unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
def verify_roster_addition():
    check(prop(pad(server),'ExpectedCount')==N+1,'Fixture PlayerState was not included by shared player-count contract')
    check(prop(pad(server),'HoldStarted')<0,'New participant without a pawn did not cancel hold')
    check(phase_is(server,0),'Roster change opened the gate')
def remove_fixture_participant():state['fixture_participant'].destroy_actor()
def verify_roster_removal():
    check(prop(pad(server),'ExpectedCount')==N,'Removed fixture participant still counted')
    check(prop(pad(server),'HoldStarted')>state['old_hold'],'Roster removal reused the previous hold start')
    check(phase_is(server,0),'Removed participant bypassed the hold')
def verify_started():
    expected=(3,2) if N==2 else (3,1) if N==3 else (4,1)
    for w in worlds:
        check(phase_is(w,1) and round_state(w)['index']==1,'Round 1 did not replicate')
        check(prop(gate(w,0),'Open') and not prop(gate(w,1),'Open'),'Entrance/exit gate state is wrong')
        check((prop(setup(w),'PlateCount'),prop(setup(w),'StatueCount'))==expected,'Scaling row does not match')
        check(prop(setup(w),'Ready'),'Puzzle setup is not ready')
        check(sum(prop(a,'Enabled') for a in by_class(w,'BP_PressurePlate'))==expected[0],'Enabled plate count wrong')
    check(len(weights())==expected[1],'Server statue spawn count wrong')
def put_weight():weights()[0].set_actor_location(unreal.Vector(400,-450,0),False,True)
def weight_tag(value):
    a=weights()[0];tags=list(prop(a,'tags'))
    tags=[t for t in tags if str(t)!='HC_PlateWeight']
    if value:tags.append(unreal.Name('HC_PlateWeight'))
    a.set_editor_property('tags',tags)
def verify_plate(slot,pressed,count=None):
    for w in worlds:
        a=plate(w,slot);top=component_named(a,'PlateTop')
        check(prop(a,'Pressed')==pressed,f'Pressed state did not replicate in {w.get_name()}')
        check(abs(top.get_editor_property('relative_location').z-(2 if pressed else 9))<.01,'RepNotify plate sink wrong')
        expected='M_HC6Pressed' if pressed else 'M_HC6Released'
        check(top.get_material(0) and top.get_material(0).get_name()==expected,'RepNotify material wrong')
        if not unreal.GameplayStatics.get_game_state(w).has_authority():
            check(prop(a,'OccupantCount')==0,'Client counted occupancy')
    if count is not None:check(prop(plate(server,slot),'OccupantCount')==count,'Server occupancy count wrong')
def leave_weight():weights()[0].set_actor_location(unreal.Vector(500,900,0),False,True)
def same_plate_approaches():
    leave_weight()
    for i,p in enumerate(state['pawns']):p.set_actor_location(unreal.Vector(250,-450+(i-.5)*55 if i<2 else 900,92.15),False,True)
def simultaneous_approaches():
    for i,p in enumerate(state['pawns']):
        v=plate(server,i).get_actor_location();p.set_actor_location(unreal.Vector(v.x-150,v.y,92.15),False,True)
    if N==2:weights()[0].set_actor_location(unreal.Vector(1200,-450,0),False,True)
def verify_clear():
    for w in worlds:
        check(phase_is(w,2),'Simultaneous presses did not clear Round 1')
        check(prop(gate(w,1),'Open'),'Cleared exit gate did not replicate')
        check(abs(component_named(gate(w,1),'GateLeaf').get_editor_property('relative_location').z-400)<.01,'Gate RepNotify transform wrong')
        check(all(prop(a,'Pressed') for a in by_class(w,'BP_PressurePlate') if prop(a,'Enabled')),'Not every enabled plate was pressed')
def reset_actors():
    stop_input()
    for i,p in enumerate(state['pawns']):p.set_actor_location(unreal.Vector(-900,i*100,92.15),False,True)
    state['old_weights']=[a.get_path_name() for a in weights()]
    gm.call_method('FailRound',args=())
    for name in ACTORS:
        for a in by_class(server,name):a.call_method('ResetForRound',args=(1,2))
    check(all(not prop(a,'Pressed') and not prop(a,'Enabled') for a in by_class(server,'BP_PressurePlate')),'Immediate plate reset failed')
    check(not prop(setup(server),'Ready') and not weights(),'Immediate setup reset failed')
    check(not prop(gate(server,1),'Open'),'Immediate gate reset failed')
    check(not prop(pad(server),'Started') and prop(pad(server),'HoldStarted')<0,'Immediate pad reset failed')
    gm.call_method('StartRound',args=(1,))
def verify_reset():
    for w in worlds:
        check(phase_is(w,1) and round_state(w)['attempt']==2,'New attempt did not replicate')
        check(prop(setup(w),'Ready'),'Setup did not respawn for the new attempt')
        check(not prop(gate(w,1),'Open'),'Reset gate remained open')
        for a in by_class(w,'BP_PressurePlate'):
            check(not prop(a,'Pressed'),'Reset plate still pressed')
            check(abs(component_named(a,'PlateTop').get_editor_property('relative_location').z-9)<.01,'Reset visual sink wrong')
    check(all(a.get_path_name() not in state['old_weights'] for a in weights()),'Old statue instance survived reset')
    check(len(weights())==(2 if N==2 else 1),'Reset statue count wrong')
    for a in weights():check(a.actor_has_tag('HC_PlateWeight'),'Reset weight lost server tag')
def rejected_reset():
    for name in ACTORS:
        for a in by_class(server,name):a.call_method('ResetForRound',args=(99,99))
    for w in worlds:
        if unreal.GameplayStatics.get_game_state(w).has_authority():continue
        for a in by_class(w,'BP_PressurePlate'):
            a.call_method('SetEnabled',args=(False,));a.call_method('ResetForRound',args=(1,99))
    check(prop(setup(server),'Ready'),'Wrong-index reset changed setup')
def verify_rejected_reset():
    verify_reset()
    check(sum(prop(a,'Enabled') for a in by_class(server,'BP_PressurePlate'))==(4 if N==4 else 3),'Unauthorized reset changed enabled plates')
steps=[
 ('warmup and identity/binding checks',1.0,None,initialize,None),
 ('pad approach settles',.7,None,None,None),
 ('all players move onto pad',.3,None,None,lambda:move_to({i:-520 for i in range(N)})),
 ('pad entry movement reaches server',.6,None,verify_pad_present,None),
 ('fixture PlayerState addition cancels hold',.5,add_fixture_participant,verify_roster_addition,None),
 ('fixture PlayerState removal starts a fresh hold',.5,remove_fixture_participant,verify_roster_removal,None),
 ('one player leaves pad through movement',.3,None,None,lambda:move_to({0:-690},1.0)),
 ('pad departure movement reaches server',.6,None,verify_departure,None),
 ('departing player returns through movement',.3,None,None,lambda:move_to({0:-520})),
 ('continuous all-player three-second hold',3.5,None,verify_started,None),
 ('server tagged stationary weight presses',.6,put_weight,lambda:verify_plate(0,True,1),None),
 ('removing weight tag while overlapping releases',.6,lambda:weight_tag(False),lambda:verify_plate(0,False,0),None),
 ('restoring weight tag while overlapping presses',.6,lambda:weight_tag(True),lambda:verify_plate(0,True,1),None),
 ('two pawn approaches settle',.7,same_plate_approaches,lambda:verify_plate(0,False,0),None),
 ('two clients enter the same plate',.3,None,None,lambda:move_to({0:400,1:400})),
 ('shared plate entry movement reaches server',.6,None,lambda:verify_plate(0,True,2),None),
 ('first pawn departure preserves second occupancy',.3,None,None,lambda:move_to({0:240})),
 ('first plate departure movement reaches server',.6,None,lambda:verify_plate(0,True,1),None),
 ('last pawn departure releases plate',.3,None,None,lambda:move_to({1:240})),
 ('last plate departure movement reaches server',.6,None,lambda:verify_plate(0,False,0),None),
 ('simultaneous puzzle approaches settle',.7,simultaneous_approaches,None,None),
 ('all enabled plates pressed through client movement',.3,None,None,lambda:move_to({i:plate(server,i).get_actor_location().x for i in range(N)})),
 ('cleared phase and gate visual replicate',.7,None,verify_clear,None),
 ('explicit actor reset and next attempt',.9,reset_actors,verify_reset,None),
 ('wrong round and client reset calls are rejected',.6,rejected_reset,verify_rejected_reset,None),
]
def own_near(targets):
    return all(abs(state['inputs'][i][1].get_controlled_pawn().get_actor_location().x-x)<=30 for i,x in targets.items())
ready={
 'warmup and identity/binding checks':lambda:len([pc for pc in unreal.ObjectIterator(unreal.PlayerController)
   if pc.get_world() in worlds and pc.is_local_controller() and pc.get_controlled_pawn() and prop(pc,'player_state')])==N,
 'all players move onto pad':lambda:prop(pad(server),'InsideCount')==N and own_near({i:-520 for i in range(N)}),
 'one player leaves pad through movement':lambda:prop(pad(server),'InsideCount')==N-1 and own_near({0:-690}),
 'departing player returns through movement':lambda:prop(pad(server),'InsideCount')==N and own_near({0:-520}),
 'two clients enter the same plate':lambda:prop(plate(server,0),'OccupantCount')==2 and own_near({0:400,1:400}),
 'first pawn departure preserves second occupancy':lambda:prop(plate(server,0),'OccupantCount')==1 and own_near({0:240}),
 'last pawn departure releases plate':lambda:prop(plate(server,0),'OccupantCount')==0 and own_near({1:240}),
 'all enabled plates pressed through client movement':lambda:phase_is(server,2),
}
def finish(error=None):
    if state['finished']:return
    state['finished']=True
    stop_input()
    result['passed']=error is None
    result['duration_seconds']=round(time.monotonic()-state['wall_start'],3)
    result['final_snapshot']=snapshot()
    if error:result['error']=error
    write_result()
    unreal.unregister_slate_post_tick_callback(state['handle'])
    unreal.log('HC6 runtime '+CONFIG['run']+' '+('PASS' if error is None else 'FAIL'))
def tick(dt):
    try:
        now=unreal.GameplayStatics.get_time_seconds(server)
        hold=prop(pad(server),'HoldStarted')
        if hold>=0:state['observed_hold_start']=hold
        if phase_is(server,1) and 'start_hold_elapsed_seconds' not in result and 'observed_hold_start' in state:
            result['start_hold_elapsed_seconds']=now-state['observed_hold_start']
            check(result['start_hold_elapsed_seconds']>=2.99,'Round started before the server three-second hold elapsed')
        if state['step']<0:
            state['step']=0;state['started']=now
        name,duration,enter,validate,drive=steps[state['step']]
        if drive:drive()
        else:stop_input()
        physically_ready=ready.get(name,lambda:True)()
        if now-state['started']>=duration and physically_ready:
            stop_input()
            if validate:validate()
            state['checks'].append({'name':name,'passed':True,'snapshot':snapshot()})
            write_result()
            state['step']+=1
            if state['step']==len(steps):finish();return
            state['started']=now
            next_enter=steps[state['step']][2]
            if next_enter:next_enter()
        elif name in ready and now-state['started']>10:
            raise TimeoutError('Movement did not reach server condition: '+name)
        if time.monotonic()-state['wall_start']>120:raise TimeoutError('Fixture test timeout')
    except Exception:finish(traceback.format_exc())
state['handle']=unreal.register_slate_post_tick_callback(tick)
