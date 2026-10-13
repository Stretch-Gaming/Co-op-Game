"""PIE-only owner/input gate. Root starts/stops/configures PIE serially.

ARGS: players=2|3|4, profile='joining'|'host_split', owner=0..N-1,
 mode='trigger_and_injected_pickup'|'observe_physical_e', timeout=45.
The physical mode observes root-delivered E; it never claims action injection
proves a physical key. Setup teleports are disclosed; round transitions use
the actual start-pad overlap and owning movement only.
"""
import hashlib,json,sys,time,traceback,types
from pathlib import Path
import unreal as ue
OUT=Path('/tmp/coop-mining')
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
assert Path(ue.Paths.project_dir()).resolve()==ROOT
ARGS=globals().get('ARGS',{})
assert ARGS.get('players') in (2,3,4)
assert ARGS.get('profile') in ('joining','host_split')
assert ARGS.get('profile')!='host_split' or ARGS['players'] in (3,4), 'This network Runtime requires a remote peer; pure two-local split is a separate gate'
mode=ARGS.get('mode','trigger_and_injected_pickup')
assert mode in ('trigger_and_injected_pickup','observe_physical_e')
registry=sys.modules.setdefault('coop_mining_registry',types.ModuleType('coop_mining_registry'))
assert not getattr(registry,'handle',None), 'Finish/stop previous mining input gate'
path=ROOT/'Tools/unreal/six_round/core/tests/runtime.py'
code=path.read_text();old="Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')"
assert code.count(old)==1
runtime=types.ModuleType('coop_mining_runtime');runtime.__file__=str(path)
exec(compile(code.replace(old,'Path('+repr(str(ROOT))+')'),str(path),'exec'),runtime.__dict__)
rt=runtime.Runtime(ARGS['players'],ARGS['profile'])
assert rt.ready() and rt.map()=='L_SixRound_Test'
assert all(not rt.dead(i) for i in range(len(rt.players)))
owner=int(ARGS.get('owner',0));assert 0<=owner<len(rt.players)
pick_cls=ue.load_asset('/Game/Hazards/FirstRoom/BP_MinePickaxe').generated_class()
near_action=ue.load_asset('/Game/Hazards/FirstRoom/Input/IA_HZ_Pickup')
swing_context=ue.load_asset('/Game/Hazards/FirstRoom/Input/IMC_HZ_Pickaxe')
hud_cls=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
assert near_action and swing_context and hud_cls
pickaxes=ue.GameplayStatics.get_all_actors_of_class(rt.server,pick_cls)
assert len(pickaxes)==1
pick=pickaxes[0]
pad=rt.actor('Six_StartPad')
clock=lambda:rt.clock()
state={'phase':'approach','at':clock(),'deadline':time.monotonic()+float(ARGS.get('timeout',45)),
       'checks':[],'mode':mode,'players':len(rt.players),'owner':owner,'phase_generation':0,'input_pulses':[],
       'fixtures':['server places all living pawns before start pad; owning movement enters trigger',
                   'server places selected owner within near-pickup distance, looking away'],
       'owner_network_evidence':rt.world_inventory,'source_runtime_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def inject_near(value):
    sub=rt.subsystems[rt.players[owner].player_state.player_id]
    sub.inject_input_vector_for_action(near_action,ue.Vector(value,0,0),[],[])

def contexts():
    results=[rt.subsystems[p.player_state.player_id].has_mapping_context(swing_context) for p in rt.players]
    return [bool(v[0] if isinstance(v,tuple) else v) for v in results]

pulse_entries={}
def pulse_send(index,action,value):
    if isinstance(action,str):rt.inject(index,action,value)
    else:
        sub=rt.subsystems[rt.players[index].player_state.player_id]
        sub.inject_input_vector_for_action(action,ue.Vector(value,0,0),[],[])
def release_phase_inputs():
    for entry in pulse_entries.values():
        pulse_send(entry['index'],entry['action'],0)
        entry['data']['phase_cleanup_zero_at']=clock()
    pulse_entries.clear()
def pulse(index,action,delay,duration):
    name=action if isinstance(action,str) else action.get_path_name();key=(index,name)
    if key not in pulse_entries:
        data={'phase':state['phase'],'generation':state['phase_generation'],'owner_index':index,
              'action':name,'delay':delay,'duration':duration,'pressed_at':None,'released_at':None,
              'positive_callbacks':0}
        pulse_entries[key]={'index':index,'action':action,'data':data};state['input_pulses'].append(data)
    data=pulse_entries[key]['data'];now=clock()
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
    return data['released_at'] is not None and clock()-data['released_at']>=settle
def phase(name):
    release_phase_inputs()
    state['phase']=name;state['at']=clock();state['phase_generation']+=1

def finish(passed,error=None):
    errors=[]
    for i in range(len(rt.players)):
        for name in ('IA_Move','IA_Drop'):
            try:rt.inject(i,name,0)
            except Exception:errors.append(traceback.format_exc())
    try:inject_near(0)
    except Exception:errors.append(traceback.format_exc())
    try:ue.unregister_slate_post_tick_callback(registry.handle)
    except Exception:errors.append(traceback.format_exc())
    registry.handle=None
    state.update(passed=bool(passed and not errors),error=error,cleanup_errors=errors,
                 method='Owning Enhanced Input action injection' if mode=='trigger_and_injected_pickup' else 'Root supplies physical E pickup; harness observes state and injects owning Drop',
                 full_mission_acceptance_pending=True)
    OUT.mkdir(parents=True,exist_ok=True)
    report=OUT/('trigger-pickaxe-'+ARGS['profile']+'-'+str(ARGS['players'])+'-owner'+str(owner)+'-'+mode+'.json')
    report.write_text(json.dumps(state,indent=2));print('COOP_MINING gate result: '+str(report))

def approach_pickaxe():
    # Park other owners away so their collision/context cannot steal the prompt.
    for i in range(len(rt.players)):
        if i!=owner:rt.place(i,(-800,-400+i*140,100))
    p=pick.get_actor_location();rt.place(owner,(p.x-120,p.y,p.z+95))
    rt.local(owner).get_controller().set_control_rotation(ue.Rotator(yaw=180))
    phase('pickup_ready')
    (OUT/'awaiting-e.json').write_text(json.dumps({'owner':owner,'controller':rt.local(owner).get_controller().get_path_name(),
         'pickaxe_location':str(p),'mode':mode,'instruction':'Root supplies E to this owning PIE window if physical mode'},indent=2))

if mode=='observe_physical_e':
    assert rt.round()['index']==1 and rt.round()['phase']==1
    approach_pickaxe()
else:
    assert rt.round()['index']==0 and rt.round()['phase']==0
    origin=pad.get_actor_location()
    for i in range(len(rt.players)):
        rt.place(i,(origin.x+(i-(len(rt.players)-1)/2)*140,origin.y-520,origin.z+100))
        rt.local(i).get_controller().set_control_rotation(ue.Rotator(yaw=90))
assert all(rt.carried(i) is None for i in range(len(rt.players)))
assert not any(contexts()), 'Start gate with free pickaxe and no owner swing mapping'

def tick(delta):
    try:
        assert time.monotonic()<state['deadline'], 'Input gate timeout'
        assert rt.ready(),'Possessed complete roster changed during bounded gate'
        assert all(not rt.dead(i) for i in range(len(rt.players))), 'Live threat killed a fixture owner; this gate did not pass'
        age=clock()-state['at']
        if state['phase']=='approach':
            # Last owner stays outside. Other owners enter through real movement.
            for i in range(len(rt.players)-1):
                rt.inject(i,'IA_Move',ue.Vector(0,1,0))
            inside=list(pad.get_overlapping_actors())
            if all(p in inside for p in rt.players[:-1]):
                for i in range(len(rt.players)-1):rt.inject(i,'IA_Move',0)
                assert rt.round()['phase']==0,'Round1 started without the complete team'
                phase('last_outside_wait')
        elif state['phase']=='last_outside_wait':
            inside=list(pad.get_overlapping_actors())
            assert rt.players[-1] not in inside
            assert rt.round()['index']==0 and rt.round()['phase']==0, 'Round starts on an incomplete team'
            if age>1.0:phase('last_owner')
        elif state['phase']=='last_owner':
            rt.inject(len(rt.players)-1,'IA_Move',ue.Vector(0,1,0))
            if rt.round()['index']==1 and rt.round()['phase']==1:
                assert all(p in pad.get_overlapping_actors() for p in rt.players), 'Transition requires complete native pad overlap'
                rt.inject(len(rt.players)-1,'IA_Move',0)
                assert rt.round()['row']==str(ARGS['players'])
                state['checks'].append('All-owner start pad waits for final owner and starts R1 with correct scaling row via owning movement')
                state['objective_wall_at']=time.monotonic();phase('objective_readback')
        elif state['phase']=='objective_readback':
            assert rt.round()['index']==1 and rt.round()['phase']==1
            expected_instruction='The first room: mine rocks, fill and push the cart, hold the plates.'
            expected_hud='Mine rocks, push the loaded cart, hold the plates.'
            snapshot={'game_states':[],'owning_huds':[]};ready=True
            for w in rt.worlds:
                gs=ue.GameplayStatics.get_game_state(w)
                text=gs.get_editor_property('AdventureInstruction') if gs else None
                snapshot['game_states'].append({'world':w.get_path_name(),'instruction':text})
                ready=ready and text==expected_instruction
            for i in range(len(rt.players)):
                pawn=rt.local(i);component=pawn.get_component_by_class(hud_cls)
                widget=component.get_editor_property('HUDWidget') if component else None
                text=widget.get_editor_property('DisplayObjective') if widget else None
                owns=widget is not None and widget.get_owning_player()==pawn.get_controller()
                snapshot['owning_huds'].append({'player_id':pawn.player_state.player_id,
                    'world':pawn.get_world().get_path_name(),'widget':widget.get_path_name() if widget else None,
                    'owned_by_controller':owns,'display_objective':text})
                ready=ready and owns and text==expected_hud
            state.setdefault('objective_first',snapshot);state['objective_latest']=snapshot
            if ready:
                state['checks'].append('Natural R1 start publishes mining/cart/plate instruction to all GameStates and every owning HUD')
                approach_pickaxe()
            else:
                assert age<3.0 and time.monotonic()-state['objective_wall_at']<5.0,('R1 mining objective did not converge',snapshot)
        elif state['phase']=='pickup_ready':
            assert rt.round()['index']==1 and rt.round()['phase']==1
            if mode=='trigger_and_injected_pickup':
                data=pulse(owner,near_action,.35,.3)
            if (mode=='observe_physical_e' or pulse_settled(data,.05)) and rt.carried(owner) and rt.carried(owner).get_class()==pick_cls:
                phase('pickup_replication')
        elif state['phase']=='pickup_replication' and age>.7:
            assert rt.carried(owner).get_class()==pick_cls
            assert all(rt.carried(i) is None for i in range(len(rt.players)) if i!=owner)
            mapping=contexts();assert mapping==[i==owner for i in range(len(rt.players))], mapping
            visible=[]
            for w in rt.worlds:
                items=ue.GameplayStatics.get_all_actors_of_class(w,pick_cls)
                assert len(items)==1
                visible.append({'world':w.get_path_name(),'pickaxe':items[0].get_path_name(),'location':str(items[0].get_actor_location())})
            state['checks'].append('Selected owner picks up near pickaxe while looking away; swing context belongs only to that owner')
            state['replicas']=visible;state['swing_context_ownership']=mapping
            phase('drop')
        elif state['phase']=='drop':
            data=pulse(owner,'IA_Drop',0,.25)
            if pulse_settled(data,.45) and rt.carried(owner) is None:
                assert not any(contexts())
                state['checks'].append('Owning Drop event releases pickaxe and removes only its swing mapping context')
                finish(True)
    except Exception:finish(False,traceback.format_exc())

registry.handle=ue.register_slate_post_tick_callback(tick);registry.state=state
RESULT={'queued':'mining-trigger-pickaxe','mode':mode,'players':ARGS['players'],'owner':owner,
        'method':state['mode'],'acceptance_pending':True}
