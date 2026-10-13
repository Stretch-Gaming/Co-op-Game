"""Root-executed PIE gate; no editor authoring or direct gameplay RPCs.

ARGS: players=2|3|4, profile=joining|host_split, case=completion|wipe|lost_rock,
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
case=args.get('case','completion'); assert case in ('completion','wipe','lost_rock')
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
       'owner_network_evidence':rt.world_inventory,'attempt':rt.round()['attempt']}
depi=0;rocki=0;target=None;stored=[];weights=[];hit_goal=0
initial_pick=prop(pick,'InitialTransform');initial_cart=cart.get_actor_location()
def phase(name):state['phase']=name;state['at']=rt.clock()
def note(text,**extra):state['checks'].append(dict(check=text,**extra))
def custom(action,value,index=owner):
    sub=rt.subsystems[rt.players[index].player_state.player_id]
    sub.inject_input_vector_for_action(action,ue.Vector(value,0,0),[],[])
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
def peers(n,field,expected):
    for w in rt.worlds:
        items=mine(n,w)
        if n=='Deposit':
            slot=int(prop(target,'Slot'));items=[a for a in items if int(prop(a,'Slot'))==slot]
        assert len(items)==1,(n,w.get_path_name(),len(items))
        assert prop(items[0],field)==expected,(n,field,w.get_path_name(),str(prop(items[0],field)),expected)
def holding_replicated(index,item):
    pid=rt.players[index].player_state.player_id
    for w in rt.worlds:
        items=[a for a in mine('Pickaxe' if item==pick else 'Rock',w) if a.get_name()==item.get_name()]
        assert len(items)==1,('missing carried replica',w.get_path_name(),item.get_name())
        replica=items[0];carrier=prop(replica,'Carrier')
        assert int(prop(replica,'CarryState'))==1 and carrier and carrier.player_state.player_id==pid
        assert replica.get_attach_parent_actor()==carrier
    local=rt.local(index);local_item=prop(local.get_component_by_class(rt.CARRY),'CarriedItem')
    assert local_item is not None and local_item.get_name()==item.get_name()
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
        age=rt.clock()-state['at'];s=rt.round();p=state['phase']
        recovery=p in ('survivor_feasible','await_failure','countdown','reset_settle')
        completing=p in ('weights_wait','door_wait','enter_maze')
        if not recovery:
            assert all(not rt.dead(i) for i in range(len(rt.players))),'Live threat killed a fixture owner'
            if not completing:assert s['index']==1 and s['phase']==1,'Round cleared/failed before the mining solution'
        if p=='pickaxe_pickup':
            custom(near,1 if .5<age<.75 else 0)
            if age>.8 and rt.carried(owner)==pick:holding_replicated(owner,pick);phase('held_ready')
        elif p=='held_ready' and age>.6:
            assert mapping()==[i==owner for i in range(len(rt.players))]
            peers('Cart','RocksNeeded',quota)
            holding_replicated(owner,pick);note('Pickaxe carried by actual input owner only; quotas configured',quota=quota,active=expected_active)
            next_deposit()
        elif p=='interact_no_hit':
            aim(owner,target,80);rt.inject(owner,'IA_Interact',1 if .5<age<.7 else 0)
            if age>1:
                assert int(prop(target,'Hits'))==0 and not prop(target,'Broken'),'Interact mined a boulder'
                note('Interact on intact boulder does not mine',slot=int(prop(target,'Slot')));phase('swing')
        elif p=='swing':
            aim(owner,target,80);custom(swing,1 if .3<age<.48 else 0)
            if age>1:
                assert int(prop(target,'Hits'))==hit_goal,('native swing hit count',hit_goal,prop(target,'Hits'))
                peers('Deposit','Hits',hit_goal)
                assert bool(prop(target,'Broken'))==(hit_goal==3),'Boulder must break on third hit only'
                if hit_goal<3:hit_goal+=1;phase('swing')
                else:
                    peers('Deposit','Broken',True);note('Exactly three owning swings break boulder on every peer',slot=int(prop(target,'Slot')))
                    rocki=0;phase('rocks_settle')
        elif p=='rocks_settle' and age>.8:next_rock()
        elif p=='rock_pickup':
            aim(mover,target,20);rt.inject(mover,'IA_Interact',1 if .55<age<.8 else 0)
            if age>1 and rt.carried(mover)==target:
                holding_replicated(mover,target)
                if int(prop(cart,'LoadedCount'))<quota:
                    state['old_loaded']=int(prop(cart,'LoadedCount'));approach(mover,cart,(-170,0,100),45);phase('rock_load')
                else:rt.place(mover,(-850,150+len(stored)*100,100));phase('rock_store_drop')
        elif p=='rock_load':
            aim(mover,cart,45);rt.inject(mover,'IA_Interact',1 if .6<age<.85 else 0)
            if age>1:
                assert int(prop(cart,'LoadedCount'))==state['old_loaded']+1,'Owning load input did not load exactly one rock'
                assert rt.carried(mover) is None and target.get_attach_parent_actor()==cart
                peers('Cart','LoadedCount',state['old_loaded']+1);note('Owning carried-rock load replicates',loaded=int(prop(cart,'LoadedCount')))
                if case=='wipe':begin_failure('wipe')
                else:phase('rock_done')
        elif p=='rock_store_drop':
            rt.inject(mover,'IA_Drop',1 if age<.2 else 0)
            if age>.7:
                assert rt.carried(mover) is None
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
            if age>.6:
                c=cart.get_actor_location();v=c-rt.players[mover].get_actor_location();gap=(v.x*v.x+v.y*v.y)**.5
                rt.inject(mover,'IA_Move',ue.Vector(0,.2 if gap>175 else 0,0));aim(mover,cart,45)
                rt.inject(mover,'IA_Interact',1)
            if prop(cart,'Arrived'):
                rt.inject(mover,'IA_Interact',0);rt.inject(mover,'IA_Move',0);park(mover)
                peers('Cart','Arrived',True);assert float(prop(cart,'Distance'))>=float(prop(cart,'TrackLength'))-.1
                note('Held owning interaction pushes full cart to track end; no early clear while plates unheld')
                # Native drops release the pickaxe before using players as weights.
                phase('pickaxe_drop')
        elif p=='pickaxe_drop':
            rt.inject(owner,'IA_Drop',1 if age<.2 else 0)
            if age>.7:
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
            for w in rt.worlds:
                peers_d=ue.GameplayStatics.get_all_actors_with_tag(w,'ConnectionDoor');assert len(peers_d)==1 and peers_d[0].get_actor_location().z>=640
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
            for w in rt.worlds:
                assert not mine('Rock',w)
                for c in mine('Cart',w):assert int(prop(c,'LoadedCount'))==0 and not prop(c,'Arrived')
                for d in mine('Deposit',w):assert not prop(d,'Broken') and int(prop(d,'Hits'))==0
                for pp in mine('Pickaxe',w):assert int(prop(pp,'CarryState'))==0
                players=ue.GameplayStatics.get_all_actors_of_class(w,rt.C)
                assert len(players)==len(rt.players),'Regroup-nearby roster not replicated completely'
                for pawn in players:
                    health=pawn.get_component_by_class(rt.H)
                    assert not prop(health,'bDead') and prop(health,'Health')==prop(health,'MaxHealth')
            note('Exactly one three-second retry restores health/checkpoints and resets mining actors on all peers');finish(True)
    except Exception:finish(False,traceback.format_exc())

registry.handle=ue.register_slate_post_tick_callback(tick);registry.state=state
RESULT={'queued':'mining-completion','case':case,'players':args['players'],'profile':args['profile'],
        'acceptance_pending':True,'warnings':state['warnings']}
