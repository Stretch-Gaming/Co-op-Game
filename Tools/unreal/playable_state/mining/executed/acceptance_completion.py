"""Root-executed PIE gate; no editor authoring or direct gameplay RPCs.

ARGS: players=2|3|4, profile=joining|host_split, case=completion|wipe|lost_rock|swing_probe,
owner=0 (pickaxe), rock_owner=1, timeout=240, enter_maze=False.
Start in R1 Playing, intact deposits/cart, pickaxe free or held by owner.
Host split requires a remote too (3/4 total) with the reused Runtime.
Approach teleports and settling of already-released rocks are explicit fixtures.
Wipe uses ApplyDamage; lost_rock also destroys free rocks as a softlock fixture.
Only game-driven failure/retry may advance Attempt or restore state.
"""
import hashlib, json, sys, time, traceback, types
from pathlib import Path
import unreal as ue

ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
OUT=Path('/tmp/coop-mining')
assert Path(ue.Paths.project_dir()).resolve()==ROOT
args=globals().get('ARGS',{})
assert args.get('players') in (2,3,4)
assert args.get('profile') in ('joining','host_split')
case=args.get('case','completion'); assert case in ('completion','wipe','lost_rock','swing_probe')
registry=sys.modules.setdefault('coop_mining_completion',types.ModuleType('coop_mining_completion'))
assert not getattr(registry,'handle',None), 'Finish previous completion gate first'
path=ROOT/'Tools/unreal/six_round/core/tests/runtime.py'
source=path.read_text(); guard="Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')"
assert source.count(guard)==1
adapted=source.replace(guard,'Path('+repr(str(ROOT))+')')
runtime=types.ModuleType('coop_mining_completion_runtime');runtime.__file__=str(path)
exec(compile(adapted,str(path),'exec'),runtime.__dict__)
rt=runtime.Runtime(args['players'],args['profile']); assert rt.ready()
assert rt.map()=='L_SixRound_Test'
assert rt.round()['index']==1 and rt.round()['phase']==1
assert all(not rt.dead(i) for i in range(len(rt.players)))
owner=int(args.get('owner',0)); mover=int(args.get('rock_owner',1))
assert 0<=owner<len(rt.players) and 0<=mover<len(rt.players) and owner!=mover
classes={n:ue.load_asset('/Game/Hazards/FirstRoom/BP_Mine'+n).generated_class()
         for n in ('Puzzle','Cart','Deposit','Pickaxe','Rock')}
def prop(obj,name):return obj.get_editor_property(name)
def mine(n,world=None):return list(ue.GameplayStatics.get_all_actors_of_class(world or rt.server,classes[n]))
assert all(len(mine(n))==1 for n in ('Puzzle','Cart','Pickaxe'))
puzzle,cart,pick=mine('Puzzle')[0],mine('Cart')[0],mine('Pickaxe')[0]
deposits=sorted(list(prop(puzzle,'Deposits')),key=lambda a:int(prop(a,'Slot')))
active=[d for d in deposits if prop(d,'Active')]
expected_active=4 if len(rt.players)==4 else 3
quota={2:6,3:7,4:9}[len(rt.players)]
assert len(active)==expected_active and int(prop(puzzle,'ActiveCount'))==expected_active
assert int(prop(cart,'RocksNeeded'))==quota and int(prop(cart,'LoadedCount'))==0
assert not prop(cart,'Arrived') and all(not prop(d,'Broken') and int(prop(d,'Hits'))==0 for d in active)
assert not mine('Rock'), 'Use a fresh intact R1 for this gate'
assert rt.carried(owner) in (None,pick) and all(rt.carried(i) is None for i in range(len(rt.players)) if i!=owner)
near=ue.load_asset('/Game/Hazards/FirstRoom/Input/IA_HZ_Pickup')
swing=ue.load_asset('/Game/Hazards/FirstRoom/Input/IA_HZ_Swing')
swing_context=ue.load_asset('/Game/Hazards/FirstRoom/Input/IMC_HZ_Pickaxe')
assert near and swing and swing_context
state={'phase':'initial','at':rt.clock(),'deadline':time.monotonic()+float(args.get('timeout',240)),
       'case':case,'players':len(rt.players),'profile':args['profile'],'owner':owner,'rock_owner':mover,
       'checks':[],'fixtures':['Server approach teleports and controller aim for owning input actions',
         'After native rock Drop only, server settles that free rock away from deposits or on a plate',
         'No direct Interact/LoadRock/TrySwing/PushTick/round/recovery RPC or plate-state setter'],
       'warnings':['Synthetic owning input does not establish physical keyboard/gamepad or Mac visual/audio acceptance',
         'Focused mining transaction does not certify continuous maze/chase or results/restart'],
       'runtime_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
       'adapted_runtime_sha256':hashlib.sha256(adapted.encode()).hexdigest(),
       'inventory_sha256':hashlib.sha256((OUT/'inventory.json').read_bytes()).hexdigest(),
       'owner_network_evidence':rt.world_inventory,'attempt':rt.round()['attempt'],
       'replication_budget':{'server_seconds':3.0,'wall_seconds':5.0},'replication_observations':[],
       'phase_generation':0,'input_pulses':[],'swing_diagnostics':[],
       'pawn_observations':[],'first_health_loss':None}
depi=0;rocki=0;target=None;stored=[];weights=[];hit_goal=0
initial_pick=prop(pick,'InitialTransform');initial_cart=cart.get_actor_location()
def phase(name):
    release_phase_inputs()
    state['phase']=name;state['at']=rt.clock();state['phase_generation']+=1
def note(text,**extra):state['checks'].append(dict(check=text,**extra))
def custom(action,value,index=owner):
    sub=rt.subsystems[rt.players[index].player_state.player_id]
    sub.inject_input_vector_for_action(action,ue.Vector(value,0,0),[],[])
pulse_entries={}
def pulse_send(index,action,value):
    if isinstance(action,str):rt.inject(index,action,value)
    else:custom(action,value,index)
def release_phase_inputs():
    for entry in pulse_entries.values():
        pulse_send(entry['index'],entry['action'],0)
        entry['data']['phase_cleanup_zero_at']=rt.clock()
    pulse_entries.clear()
def pulse(index,action,delay,duration):
    name=action if isinstance(action,str) else action.get_path_name();key=(index,name)
    if key not in pulse_entries:
        data={'phase':state['phase'],'generation':state['phase_generation'],'owner_index':index,
              'action':name,'delay':delay,'duration':duration,'pressed_at':None,'released_at':None,
              'positive_callbacks':0}
        pulse_entries[key]={'index':index,'action':action,'data':data};state['input_pulses'].append(data)
    data=pulse_entries[key]['data'];now=rt.clock()
    if data['released_at'] is not None:pulse_send(index,action,0)
    elif data['pressed_at'] is None:
        if now-state['at']<delay:pulse_send(index,action,0)
        else:
            pulse_send(index,action,1);data.update(pressed_at=now,pressed_wall_at=time.monotonic(),positive_callbacks=1)
    elif now-data['pressed_at']>=duration:
        pulse_send(index,action,0);data.update(released_at=now,released_wall_at=time.monotonic())
    else:
        pulse_send(index,action,1);data['positive_callbacks']+=1
    return data
def pulse_settled(data,settle):
    return data['released_at'] is not None and rt.clock()-data['released_at']>=settle
def mapping():
    values=[rt.subsystems[p.player_state.player_id].has_mapping_context(swing_context) for p in rt.players]
    return [bool(v[0] if isinstance(v,tuple) else v) for v in values]
def park(index):rt.place(index,(-850,-350+index*140,100))
def aim(index,actor,height=30):
    camera=rt.local(index).get_component_by_class(ue.CameraComponent)
    rt.local(index).get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(
        camera.get_world_location(),actor.get_actor_location()+ue.Vector(0,0,height)))
def approach(index,actor,offset=(-190,0,100),height=30):
    p=actor.get_actor_location();rt.place(index,(p.x+offset[0],p.y+offset[1],p.z+offset[2]));aim(index,actor,height)
class ReplicationPending(Exception):pass
pending={}
def replicated(label,snapshot,ready):
    # Server acceptance is checked by the caller. Independent replicated fields
    # can arrive on later frames; polling must neither repeat input nor set state.
    key=(state['phase'],label)
    wait=pending.get(key)
    if wait is None:
        wait={'phase':state['phase'],'label':label,'at':rt.clock(),'wall_at':time.monotonic(),
              'first':snapshot,'latest':snapshot,'polls':0,'converged':False}
        pending[key]=wait;state['replication_observations'].append(wait)
    wait.update(latest=snapshot,polls=wait['polls']+1,converged=bool(ready),
                server_elapsed=rt.clock()-wait['at'],wall_elapsed=time.monotonic()-wait['wall_at'])
    if ready:
        wait['converged']=True;return
    assert wait['server_elapsed']<3.0 and wait['wall_elapsed']<5.0,('Replication did not converge',wait)
    raise ReplicationPending(label)
def peers(n,field,expected):
    snapshot=[];ready=True
    for w in rt.worlds:
        items=mine(n,w)
        if n=='Deposit':
            slot=int(prop(target,'Slot'));items=[a for a in items if int(prop(a,'Slot'))==slot]
        values=[prop(a,field) for a in items]
        snapshot.append({'world':w.get_path_name(),'matches':[a.get_path_name() for a in items],
                         'field':field,'observed':values,'expected':expected})
        ready=ready and len(items)==1 and values[0]==expected
    label=n+(':'+str(slot) if n=='Deposit' else '')+':'+field+':'+str(expected)
    replicated(label,snapshot,ready)
def holding_replicated(index,item):
    pid=rt.players[index].player_state.player_id;snapshot=[];ready=True
    assert rt.carried(index)==item,'Authoritative owner lost the accepted carried item'
    assert int(prop(item,'CarryState'))==1 and prop(item,'Carrier')==rt.players[index] \
        and item.get_attach_parent_actor()==rt.players[index],'Authoritative carried state differs from accepted owner'
    for w in rt.worlds:
        # Spawned actor names depend on each world's creation order. Resolve the
        # replicated actor reference on this owner's peer component instead.
        items=mine('Pickaxe' if item==pick else 'Rock',w)
        pawns=[p for p in ue.GameplayStatics.get_all_actors_of_class(w,rt.C)
               if p.player_state and p.player_state.player_id==pid]
        peer=pawns[0] if len(pawns)==1 else None
        held=prop(peer.get_component_by_class(rt.CARRY),'CarriedItem') if peer else None
        observed=[]
        for replica in items:
            carrier=prop(replica,'Carrier');player_state=carrier.player_state if carrier else None
            parent=replica.get_attach_parent_actor()
            observed.append({'actor':replica.get_path_name(),'carry_state':int(prop(replica,'CarryState')),
              'carrier':carrier.get_path_name() if carrier else None,
              'carrier_player_id':player_state.player_id if player_state else None,
              'attach_parent':parent.get_path_name() if parent else None,
              'attached_to_carrier':carrier is not None and parent==carrier})
        snapshot.append({'world':w.get_path_name(),'server_target':item.get_path_name(),
                         'expected_player_id':pid,'owner_pawn_count':len(pawns),
                         'owner_component_carried_item':held.get_path_name() if held else None,
                         'candidates':observed})
        ready=ready and peer is not None and held is not None and held in items and \
            int(prop(held,'CarryState'))==1 and prop(held,'Carrier')==peer and \
            held.get_attach_parent_actor()==peer
    replicated('holding:'+item.get_name(),snapshot,ready)
def empty_hands_replicated(index):
    pid=rt.players[index].player_state.player_id;snapshot=[];ready=True
    assert rt.carried(index) is None,'Authoritative release did not clear carried item'
    for w in rt.worlds:
        pawns=[p for p in ue.GameplayStatics.get_all_actors_of_class(w,rt.C)
               if p.player_state and p.player_state.player_id==pid]
        peer=pawns[0] if len(pawns)==1 else None
        held=prop(peer.get_component_by_class(rt.CARRY),'CarriedItem') if peer else None
        snapshot.append({'world':w.get_path_name(),'expected_player_id':pid,'owner_pawn_count':len(pawns),
                         'owner_component_carried_item':held.get_path_name() if held else None})
        ready=ready and peer is not None and held is None
    replicated('released:'+str(pid)+':'+target.get_name(),snapshot,ready)
def capture_swing(stage):
    # Read-only replay of the native ServerSwing query, not TrySwing/interaction.
    # Inventory: carrier eyes + forward45..330, radius25, default Query1,
    # simple collision, ignore-self (the pickaxe), empty explicit ignore array.
    row={'stage':stage,'at':rt.clock(),'goal':hit_goal,'pulse_generation':state['phase_generation']}
    state['swing_diagnostics'].append(row)
    try:
        def vector(v):return [v.x,v.y,v.z]
        def rotation(r):return {'pitch':r.pitch,'yaw':r.yaw,'roll':r.roll}
        def actor(a):return {'path':a.get_path_name(),'class':a.get_class().get_name(),'label':a.get_actor_label()} if a else None
        pawn=rt.players[owner];local=rt.local(owner)
        eye,rot=pawn.get_actor_eyes_view_point();forward=ue.MathLibrary.get_forward_vector(rot)
        start=eye+forward*45.;end=eye+forward*330.
        row.update(target=actor(target),target_location=vector(target.get_actor_location()),slot=int(prop(target,'Slot')),
            target_state={n:prop(target,n) for n in ('Active','Broken','Hits','HitsNeeded')},
            server_pawn=actor(pawn),server_position=vector(pawn.get_actor_location()),server_eye=vector(eye),server_eye_rotation=rotation(rot),
            server_control_rotation=rotation(pawn.get_controller().get_control_rotation()),
            trace={'start':vector(start),'end':vector(end),'radius':25.,'channel':'TraceTypeQuery1','trace_complex':False,
                   'ignore_self':'pickaxe','actors_to_ignore':[]})
        hit=ue.SystemLibrary.sphere_trace_single(pick,start,end,25.,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],ue.DrawDebugTrace.NONE,True)
        data=hit.to_dict() if hit else {}
        contacts={}
        for name in ('blocking_hit','initial_overlap','start_penetrating','time','distance','location','impact_point','normal','impact_normal','trace_start','trace_end'):
            if name in data:
                value=data[name];contacts[name]=vector(value) if hasattr(value,'x') else value if isinstance(value,(str,int,float,bool,type(None))) else str(value)
        component=data.get('hit_component');camera=local.get_component_by_class(ue.CameraComponent)
        local_eye,local_rot=local.get_actor_eyes_view_point();peer_pick=prop(local.get_component_by_class(rt.CARRY),'CarriedItem')
        row['trace'].update(hit_actor=actor(data.get('hit_actor')),hit_component=component.get_path_name() if component else None,contact=contacts)
        row.update(
            owning_position=vector(local.get_actor_location()),owning_eye=vector(local_eye),owning_eye_rotation=rotation(local_rot),
            owning_control_rotation=rotation(local.get_controller().get_control_rotation()),
            camera_location=vector(camera.get_world_location()),camera_rotation=rotation(camera.get_world_rotation()),
            aimed_point=vector(target.get_actor_location()+ue.Vector(0,0,80)),
            owning_focus=actor(prop(local,'FocusedTarget')),server_focus=actor(prop(pawn,'FocusedTarget')),
            pickaxe=actor(pick),pickaxe_state={n:prop(pick,n) for n in ('CarryState','LastSwingTime','LocalSwingTime')},
            pickaxe_carrier=actor(prop(pick,'Carrier')),pickaxe_attach_parent=actor(pick.get_attach_parent_actor()),
            owning_carried_item=actor(peer_pick),owning_pickaxe_state={n:prop(peer_pick,n) for n in ('CarryState','LastSwingTime','LocalSwingTime')} if peer_pick else None,
            swing_context_ownership=mapping(),
            input_pulses=[dict(p) for p in state['input_pulses'] if p['generation']==state['phase_generation']])
        row['attached_pickaxes']=[actor(a) for a in pawn.get_attached_actors() if a.actor_has_tag('HZ_Pickaxe')]
        validation={'pickaxe_location':vector(pick.get_actor_location()),
            'pawn_to_pickaxe_distance':(pawn.get_actor_location()-pick.get_actor_location()).length(),
            'interaction_blocked':prop(pawn,'InteractionBlocked'),'downed_tag':pawn.actor_has_tag('Downed'),
            'can_interact_derived_from_saved_graph':int(prop(pick,'CarryState'))==0 or pick.get_attach_parent_actor()==pawn}
        row['character_use_validation']=validation
        validation['use_allowed_return']=pawn.call_method('UseAllowed',args=(pick,))
        validation['pickaxe_can_interact_return']=pick.call_method('CanInteract',args=(pawn,))
        use_hit=ue.SystemLibrary.line_trace_single(pawn,eye,pick.get_actor_location(),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],ue.DrawDebugTrace.NONE,True)
        use_data=use_hit.to_dict() if use_hit else {}
        validation['eye_to_pickaxe_los']={'start':vector(eye),'end':vector(pick.get_actor_location()),
            'channel':'TraceTypeQuery1','trace_complex':False,'ignore_self':'character','actors_to_ignore':[],
            'blocking_hit':bool(use_data.get('blocking_hit',False)),'hit_actor':actor(use_data.get('hit_actor')),
            'hit_component':use_data['hit_component'].get_path_name() if use_data.get('hit_component') else None,
            'impact_point':vector(use_data['impact_point']) if use_data.get('impact_point') is not None else None}
        owners=[];row['network_ownership']=owners
        for world in rt.worlds:
            info={'world':world.get_path_name(),'pickaxes':[],'carrier_pawns':[]};owners.append(info)
            def owner_chain(a):
                chain=[];seen=[]
                for depth in range(6):
                    a=a.get_owner() if a else None
                    if a is None or a in seen:break
                    seen.append(a);chain.append(actor(a))
                return chain
            for item in mine('Pickaxe',world):
                info['pickaxes'].append({'actor':actor(item),'net_owner':actor(item.get_owner()),'owner_chain':owner_chain(item),
                     'carrier':actor(prop(item,'Carrier')),'attach_parent':actor(item.get_attach_parent_actor()),
                     'bound_controller':actor(prop(item,'BoundController')),
                     'carry_state':int(prop(item,'CarryState')),'last_swing_time':prop(item,'LastSwingTime'),
                     'local_swing_time':prop(item,'LocalSwingTime')})
            for pp in ue.GameplayStatics.get_all_actors_of_class(world,rt.C):
                if pp.player_state and pp.player_state.player_id==pawn.player_state.player_id:
                    info['carrier_pawns'].append({'actor':actor(pp),'owner_chain':owner_chain(pp),
                      'controller':actor(pp.get_controller()),'locally_controlled':pp.is_locally_controlled(),
                      'taken_protected':prop(pp,'bTakenProtected'),'interaction_blocked':prop(pp,'InteractionBlocked'),
                      'dead':prop(pp.get_component_by_class(rt.H),'bDead'),
                      'active_target':actor(prop(pp,'ActiveTarget')),'active_use':prop(pp,'ActiveUse')})
    except Exception:row['diagnostic_error']=traceback.format_exc()
def observe_pawns():
    row={'at':rt.clock(),'phase':state['phase'],'owners':[]}
    try:
        def vector(v):return [v.x,v.y,v.z]
        def item(a):return {'path':a.get_path_name(),'class':a.get_class().get_name(),'location':vector(a.get_actor_location())} if a else None
        for i,pawn in enumerate(rt.players):
            health=pawn.get_component_by_class(rt.H);movement=pawn.character_movement;held=rt.carried(i)
            row['owners'].append({'index':i,'player_id':pawn.player_state.player_id,'pawn':item(pawn),
                'velocity':vector(movement.velocity),'movement_mode':str(movement.movement_mode),
                'health':prop(health,'Health'),'max_health':prop(health,'MaxHealth'),
                'dead':bool(prop(health,'bDead')),'is_dead_query':bool(health.call_method('IsDead')),
                'carried_item':item(held),'carried_carrier':item(prop(held,'Carrier')) if held else None,
                'owning_position':vector(rt.local(i).get_actor_location())})
        row['last_target']=item(target)
        if target and target.get_class() in (classes['Rock'],classes['Pickaxe']):
            row['target_carry_state']=int(prop(target,'CarryState'));row['target_carrier']=item(prop(target,'Carrier'))
    except Exception:row['diagnostic_error']=traceback.format_exc()
    previous=state['pawn_observations'][-1] if state['pawn_observations'] else None
    if previous and state['first_health_loss'] is None:
        old={p['player_id']:p for p in previous['owners']}
        changed=[p for p in row['owners'] if p['player_id'] in old and
                 (p['health']<old[p['player_id']]['health'] or (p['dead'] and not old[p['player_id']]['dead']))]
        if changed:state['first_health_loss']={'before':previous,'after':row,'changed_player_ids':[p['player_id'] for p in changed]}
    state['pawn_observations'].append(row);state['pawn_observations']=state['pawn_observations'][-8:]
    return row
def capture_owner_loss(row):
    report={'pawns':row,'nearby_threats':[],'radius_cm':2000,'damage_cause_established':False}
    state['owner_loss_snapshot']=report
    try:
        positions=[p.get_actor_location() for p in rt.players]
        for a in ue.GameplayStatics.get_all_actors_of_class(rt.server,ue.Actor):
            label=a.get_actor_label();kind=a.get_class().get_name()
            if not any(t in (label+' '+kind).lower() for t in ('ghost','cavebeing','trap','hazard','spike','dart','swing','pit','kill','death')):continue
            distances=[(a.get_actor_location()-p).length() for p in positions]
            if min(distances)>2000:continue
            loc=a.get_actor_location();overlaps=a.get_overlapping_actors()
            report['nearby_threats'].append({'path':a.get_path_name(),'label':label,'class':kind,
                'location':[loc.x,loc.y,loc.z],'distances_to_owners':distances,
                'overlapping_owner_ids':[p.player_state.player_id for p in rt.players if p in overlaps]})
    except Exception:report['diagnostic_error']=traceback.format_exc()
def settle(rock,pos):
    assert int(prop(rock,'CarryState'))==0 and not rock.get_attach_parent_actor()
    # Physics settling is setup only; native Drop must have supplied the free state/tag.
    rock.set_actor_location(ue.Vector(*pos),False,True)
    rock.static_mesh_component.set_physics_linear_velocity(ue.Vector(),False)
    rock.static_mesh_component.set_physics_angular_velocity_in_degrees(ue.Vector(),False)
def next_deposit():
    global target,hit_goal
    target=active[depi];approach(owner,target,(-230,0,100),80)
    hit_goal=1;phase('interact_no_hit')
def next_rock():
    global target
    rocks=list(prop(active[depi],'Rocks'));assert len(rocks)==int(prop(active[depi],'RockCount'))
    target=rocks[rocki];assert int(prop(target,'CarryState'))==0
    approach(mover,target,(-155,0,100),20);phase('rock_pickup')
def begin_failure(kind):
    state['failure_case']=kind;state['old_attempt']=rt.round()['attempt']
    if kind=='wipe':
        state['fixtures'].append('ApplyDamage kills all owners after native first-rock loading')
        for i in range(len(rt.players)):rt.kill(i)
    else:
        state['fixtures'].append('ApplyDamage leaves one survivor; after proving spare-rock feasibility, free mined rocks destroyed')
        for i in range(1,len(rt.players)):rt.kill(i)
        phase('survivor_feasible');return
    phase('await_failure')
def finish(passed,error=None):
    errors=[]
    try:rt.cleanup_input()
    except Exception:errors.append(traceback.format_exc())
    for action in (near,swing):
        try:custom(action,0)
        except Exception:errors.append(traceback.format_exc())
    try:ue.unregister_slate_post_tick_callback(registry.handle)
    except Exception:errors.append(traceback.format_exc())
    registry.handle=None
    state.update(passed=bool(passed and not errors),error=error,cleanup_errors=errors,
                 ending_round=rt.round(),method='Real owning Enhanced Input actions with disclosed approach/settling fixtures',
                 full_mission_acceptance_pending=True)
    report=OUT/('completion-'+case+'-'+args['profile']+'-'+str(args['players'])+'-owner'+str(owner)+'.json')
    report.write_text(json.dumps(state,indent=2));print('COOP_MINING completion result: '+str(report))

for i in range(len(rt.players)):park(i)
if rt.carried(owner)==pick:phase('held_ready')
else:approach(owner,pick,(-120,0,95));phase('pickaxe_pickup')

def tick(delta):
    global depi,rocki,target,hit_goal
    try:
        assert time.monotonic()<state['deadline'],'Completion gate timeout'
        assert rt.ready(),'Roster/possession changed'
        pawn_row=observe_pawns()
        age=rt.clock()-state['at'];s=rt.round();p=state['phase']
        recovery=p in ('survivor_feasible','await_failure','countdown','reset_settle')
        completing=p in ('weights_wait','door_wait','enter_maze')
        if not recovery:
            if any(rt.dead(i) for i in range(len(rt.players))):
                capture_owner_loss(pawn_row)
                raise AssertionError('Live threat killed a fixture owner; owner_loss_snapshot records pose/health/nearby actors')
            if not completing:assert s['index']==1 and s['phase']==1,'Round cleared/failed before the mining solution'
        if p=='pickaxe_pickup':
            data=pulse(owner,near,.5,.25)
            if pulse_settled(data,.05) and rt.carried(owner)==pick:holding_replicated(owner,pick);phase('held_ready')
        elif p=='held_ready' and age>.6:
            assert mapping()==[i==owner for i in range(len(rt.players))]
            peers('Cart','RocksNeeded',quota)
            holding_replicated(owner,pick);note('Pickaxe carried by actual input owner only; quotas configured',quota=quota,active=expected_active)
            next_deposit()
        elif p=='interact_no_hit':
            aim(owner,target,80);data=pulse(owner,'IA_Interact',.5,.2)
            if pulse_settled(data,.3):
                assert int(prop(target,'Hits'))==0 and not prop(target,'Broken'),'Interact mined a boulder'
                note('Interact on intact boulder does not mine',slot=int(prop(target,'Slot')));phase('swing')
        elif p=='swing':
            aim(owner,target,80);data=pulse(owner,swing,.3,.18)
            if int(prop(target,'Slot'))==1 and hit_goal==1 and data['positive_callbacks']==1 and data['released_at'] is None:
                capture_swing('second_slot_first_positive_injection')
            if pulse_settled(data,.52):
                if int(prop(target,'Hits'))!=hit_goal:capture_swing('before_native_hit_count_assertion')
                assert int(prop(target,'Hits'))==hit_goal,('native swing hit count',hit_goal,prop(target,'Hits'))
                peers('Deposit','Hits',hit_goal)
                assert bool(prop(target,'Broken'))==(hit_goal==3),'Boulder must break on third hit only'
                if case=='swing_probe' and depi==1:
                    capture_swing('focused_second_deposit_one_hit_success')
                    note('Focused two-deposit probe: first boulder broken, no rock interactions, one owning swing hits second boulder')
                    finish(True);return
                if hit_goal<3:hit_goal+=1;phase('swing')
                else:
                    peers('Deposit','Broken',True);note('Exactly three owning swings break boulder on every peer',slot=int(prop(target,'Slot')))
                    if case=='swing_probe':
                        state['fixtures'].append('Focused diagnostic skips all rock pickup/loading; rover remains parked')
                        depi+=1;next_deposit()
                    else:rocki=0;phase('rocks_settle')
        elif p=='rocks_settle' and age>.8:next_rock()
        elif p=='rock_pickup':
            aim(mover,target,20);data=pulse(mover,'IA_Interact',.55,.25)
            if pulse_settled(data,.2) and rt.carried(mover)==target:
                holding_replicated(mover,target)
                if int(prop(cart,'LoadedCount'))<quota:
                    state['old_loaded']=int(prop(cart,'LoadedCount'));approach(mover,cart,(-170,0,100),45);phase('rock_load')
                else:rt.place(mover,(-850,150+len(stored)*100,100));phase('rock_store_drop')
        elif p=='rock_load':
            aim(mover,cart,45);data=pulse(mover,'IA_Interact',.6,.25)
            if pulse_settled(data,.15):
                assert int(prop(cart,'LoadedCount'))==state['old_loaded']+1,'Owning load input did not load exactly one rock'
                assert rt.carried(mover) is None and target.get_attach_parent_actor()==cart
                peers('Cart','LoadedCount',state['old_loaded']+1);empty_hands_replicated(mover)
                note('Owning carried-rock load replicates',loaded=int(prop(cart,'LoadedCount')))
                if case=='wipe':begin_failure('wipe')
                else:phase('rock_done')
        elif p=='rock_store_drop':
            data=pulse(mover,'IA_Drop',0,.2)
            if pulse_settled(data,.5):
                assert rt.carried(mover) is None
                empty_hands_replicated(mover)
                settle(target,(-850,150+len(stored)*100,35));stored.append(target);phase('rock_done')
        elif p=='rock_done':
            rocki+=1
            if rocki<int(prop(active[depi],'RockCount')):next_rock()
            else:park(mover);phase('reveal_wait')
        elif p=='reveal_wait' and age>.7:
            d=active[depi];assert prop(d,'Revealed') and prop(prop(d,'Plate'),'Enabled'),'Native removing all rocks did not reveal plate'
            note('All rocks removed by owning pickup; plate reveals without state setter',slot=int(prop(d,'Slot')))
            depi+=1
            if depi<len(active):next_deposit()
            else:
                assert int(prop(cart,'LoadedCount'))==quota
                assert len(stored)==sum(int(prop(d,'RockCount')) for d in active)-quota
                for i in range(len(rt.players)):park(i)
                if case=='lost_rock':begin_failure('lost_rock')
                else:
                    approach(mover,cart,(-180,0,100),45);state['push_from']=float(prop(cart,'Distance'));phase('push')
        elif p=='push':
            # Only owning movement follows the cart after the single approach fixture.
            if age>.6 and not prop(cart,'Arrived'):
                c=cart.get_actor_location();v=c-rt.players[mover].get_actor_location();gap=(v.x*v.x+v.y*v.y)**.5
                rt.inject(mover,'IA_Move',ue.Vector(0,.2 if gap>175 else 0,0));aim(mover,cart,45)
                rt.inject(mover,'IA_Interact',1)
            if prop(cart,'Arrived'):
                rt.inject(mover,'IA_Interact',0);rt.inject(mover,'IA_Move',0)
                peers('Cart','Arrived',True);assert float(prop(cart,'Distance'))>=float(prop(cart,'TrackLength'))-.1
                park(mover)
                note('Held owning interaction pushes full cart to track end; no early clear while plates unheld')
                # Native drops release the pickaxe before using players as weights.
                phase('pickaxe_drop')
        elif p=='pickaxe_drop':
            data=pulse(owner,'IA_Drop',0,.2)
            if pulse_settled(data,.5):
                assert rt.carried(owner) is None and not any(mapping())
                # Each live owner stands on one plate; remaining plates use released spare rocks.
                needed=max(0,len(active)-len(rt.players));assert len(stored)>=needed
                for j in range(needed):
                    plate=prop(active[len(rt.players)+j],'Plate');v=plate.get_actor_location()
                    settle(stored[j],(v.x,v.y,v.z+30));weights.append(stored[j])
                state['fixtures'].append('Released spare rocks settled onto extra plates; owner positions supply native overlaps')
                for i in range(1,len(rt.players)):
                    v=prop(active[i],'Plate').get_actor_location();rt.place(i,(v.x,v.y,v.z+100))
                phase('last_plate_withheld')
        elif p=='last_plate_withheld':
            assert s['index']==1 and s['phase']==1,'Cart + partial plate weights cleared early'
            assert not prop(prop(active[0],'Plate'),'Pressed'),'Withheld first plate must remain unpressed'
            if age>1.2:
                assert all(prop(prop(d,'Plate'),'Pressed') for d in active[1:]),'Other native plate weights did not settle'
                note('Arrived cart and every other plate held cannot clear while first plate is unpressed')
                v=prop(active[0],'Plate').get_actor_location();rt.place(0,(v.x,v.y,v.z+100));phase('weights_wait')
        elif p=='weights_wait':
            if s['phase']==2 and s['index']==1:
                assert prop(cart,'Arrived') and all(prop(prop(d,'Plate'),'Pressed') for d in active)
                note('Cart arrival alone cannot clear; all native plate overlaps clear R1 exactly once')
                phase('door_wait')
            elif age>3:raise AssertionError('Valid cart + plate solution did not clear R1')
        elif p=='door_wait' and age>1.5:
            doors=ue.GameplayStatics.get_all_actors_with_tag(rt.server,'ConnectionDoor');assert len(doors)==1
            assert doors[0].get_actor_location().z>=649,'Sole north door failed to open'
            snapshot=[];ready=True
            for w in rt.worlds:
                peers_d=ue.GameplayStatics.get_all_actors_with_tag(w,'ConnectionDoor')
                heights=[a.get_actor_location().z for a in peers_d]
                snapshot.append({'world':w.get_path_name(),'door_z':heights,'minimum_z':640})
                ready=ready and len(heights)==1 and heights[0]>=640
            replicated('north_door_open',snapshot,ready)
            note('Sole existing north connection door opens on every peer after mining clear')
            if args.get('enter_maze'):
                for i in range(len(rt.players)):
                    rt.place(i,(325+(i-(len(rt.players)-1)/2)*60,1050,100))
                    rt.local(i).get_controller().set_control_rotation(ue.Rotator(yaw=90))
                phase('enter_maze')
            else:finish(True)
        elif p=='enter_maze':
            for i in range(len(rt.players)):rt.inject(i,'IA_Move',ue.Vector(0,1,0))
            if s['index']==2 and s['phase']==1:
                note('All owners walk through north doorway and native mouth trigger starts R2');finish(True)
        elif p=='survivor_feasible':
            assert s['index']==1 and s['phase']==1 and s['attempt']==state['old_attempt'],'Feasible survivor + spare rocks failed prematurely'
            assert len(rt.alive_roster())==1
            if age>1.2:
                note('One survivor with available spare rocks remains in Playing; old statue heuristic is absent')
                available=sorted([a for a in mine('Rock') if int(prop(a,'CarryState'))==0
                    and a.get_attach_parent_actor()!=cart and a.get_actor_location().z>=-1700],key=lambda a:a.get_name())
                assert all(prop(d,'Broken') for d in active),'This boundary fixture requires no spawnable reserve'
                required=max(0,int(prop(cart,'RocksNeeded'))-int(prop(cart,'LoadedCount')))+max(0,len(active)-1)
                loss=len(available)-required+1
                assert 0<loss<=len(available)
                note('Minimal free-rock loss crosses mining feasibility boundary',available=len(available),required=required,lost=loss,remaining=len(available)-loss)
                for a in available[:loss]:a.destroy_actor()
                phase('await_failure')
        elif p=='await_failure':
            assert s['index']==1 and s['attempt']==state['old_attempt']
            if s['phase']==3:
                assert 0<s['ends']-rt.clock()<=3.2
                state['retry_deadline']=s['ends'];note('Game detects '+case+' and starts three-second retry');phase('countdown')
            elif age>2:raise AssertionError('Game did not detect mining '+case+' within monitor budget')
        elif p=='countdown':
            if rt.clock()<state['retry_deadline']-.06:assert s['phase']==3 and s['attempt']==state['old_attempt']
            if s['attempt']>state['old_attempt']:
                assert rt.clock()>=state['retry_deadline']-.06
                rt.assert_recovered(1,state['old_attempt']);phase('reset_settle')
        elif p=='reset_settle' and age>.8:
            rt.assert_recovered(1,state['old_attempt'])
            assert not mine('Rock') and int(prop(cart,'LoadedCount'))==0 and not prop(cart,'Arrived')
            assert (cart.get_actor_location()-initial_cart).length()<1 and float(prop(cart,'Distance'))==0
            assert int(prop(pick,'CarryState'))==0 and all(rt.carried(i) is None for i in range(len(rt.players)))
            assert (pick.get_actor_location()-initial_pick.translation).length()<140
            for d in active:
                assert not prop(d,'Broken') and int(prop(d,'Hits'))==0 and not prop(d,'Revealed') and not prop(prop(d,'Plate'),'Enabled')
            snapshot=[];ready=True
            for w in rt.worlds:
                rocks=[a.get_path_name() for a in mine('Rock',w)]
                carts=[{'loaded':int(prop(c,'LoadedCount')),'arrived':bool(prop(c,'Arrived'))} for c in mine('Cart',w)]
                deposits_w=[{'slot':int(prop(d,'Slot')),'broken':bool(prop(d,'Broken')),'hits':int(prop(d,'Hits'))} for d in mine('Deposit',w)]
                picks=[int(prop(pp,'CarryState')) for pp in mine('Pickaxe',w)]
                players=ue.GameplayStatics.get_all_actors_of_class(w,rt.C)
                health_w=[]
                for pawn in players:
                    health=pawn.get_component_by_class(rt.H)
                    health_w.append({'player_id':pawn.player_state.player_id if pawn.player_state else None,
                         'dead':bool(prop(health,'bDead')),'health':prop(health,'Health'),'max_health':prop(health,'MaxHealth')})
                snapshot.append({'world':w.get_path_name(),'rocks':rocks,'carts':carts,'deposits':deposits_w,
                                 'pick_carry_states':picks,'health':health_w})
                ready=ready and not rocks and len(carts)==1 and all(c['loaded']==0 and not c['arrived'] for c in carts) \
                    and len(deposits_w)==len(deposits) and all(not d['broken'] and d['hits']==0 for d in deposits_w) \
                    and len(picks)==1 and picks[0]==0 and len(health_w)==len(rt.players) \
                    and {h['player_id'] for h in health_w}=={p.player_state.player_id for p in rt.players} \
                    and all(not h['dead'] and h['health']==h['max_health'] for h in health_w)
            replicated('retry_resources_and_roster',snapshot,ready)
            note('Exactly one three-second retry restores health/checkpoints and resets mining actors on all peers');finish(True)
    except ReplicationPending:pass
    except Exception:finish(False,traceback.format_exc())

registry.handle=ue.register_slate_post_tick_callback(tick);registry.state=state
RESULT={'queued':'mining-completion','case':case,'players':args['players'],'profile':args['profile'],
        'acceptance_pending':True,'warnings':state['warnings']}
