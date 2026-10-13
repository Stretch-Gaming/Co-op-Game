"""Serialized owning-input ghost safety gate; root controls the editor.

Prerequisites: fresh L_SixRound_Test Lobby, 2/3/4 Play As Client owners, or a
host-split pair plus 0/1/2 joining owners. No other test callback. Parent starts
and stops PIE. Tests use owning F/Q input; initial poses, runtime ghost spawn,
lethal damage and destroyed-pawn cases are explicitly marked fixtures.

Set ARGS or Saved/PlayableState/Ghosts/args.json:
 {"players":2,"profile":"joining","owner_ordinal":0,"case":"retarget_death"}
Cases: retarget_death, all_dead, flare_all_safe, destroyed_target, flare_backoff.
Each case needs a fresh PIE session. No production target/dead/scaling/stock writes.
No asset save/compile, editor-map change, StartRound/FailRound or ResetHealth call.
"""
import json, math, sys, time, traceback
from pathlib import Path
import unreal as ue
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from Tools.unreal.playable_state.ghosts.context import ROOT, QUEUE, guard
guard()
from Tools.unreal.playable_state.ghosts.ghost_runtime_support import Harness
args=globals().get('ARGS')
if not args:
    args=json.loads((QUEUE / 'args.json').read_text())
args=dict(args);args.setdefault('timeout',45)
case=args.get('case','retarget_death')
assert case in ('retarget_death','all_dead','flare_all_safe','destroyed_target','flare_backoff')
h=Harness(args,'ghost-'+case)
assert ue.GameplayStatics.get_current_level_name(h.server,True)=='L_SixRound_Test'
assert h.round()['index']==0 and h.round()['phase']==0, 'Fresh Lobby required for isolated ghost target gates'
GHOST=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
assert not ue.GameplayStatics.get_all_actors_of_class(h.server,GHOST), 'Do not relocate/destroy existing production ghosts'
assert not ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['flare']), 'Fresh case needs no pre-existing flares'
pid=h.ids[int(args.get('owner_ordinal',0))]
assert all(not h.prop(h.pawn(h.server,i),'health','bDead') for i in h.ids)
assert all(not h.pawn(h.server,i).get_editor_property('bTakenProtected') for i in h.ids)
assert all(not h.pawn(h.server,i).call_method('IsCarryingHeavy') for i in h.ids)
original_positions={i:h.pawn(h.server,i).get_actor_transform() for i in h.ids}
state={'samples':[], 'case':case,'baseline_health':{},'deadline_decreased':False}
old_finish=h.finish

def valid(obj):
    if obj is None:return False
    try:return bool(ue.SystemLibrary.is_valid(obj))
    except Exception:return False

def label(obj):
    if not valid(obj):return None
    return obj.get_path_name()

def living_target(target):
    if not valid(target):return False
    health=target.get_component_by_class(h.classes['health'])
    return valid(health) and not bool(health.call_method('IsDead'))

def cleanup_fixture():
    ghost=state.get('ghost')
    if valid(ghost):ghost.destroy_actor()
    # Restore only surviving actors, without resurrecting or possessing anyone.
    for pawn in h.pawns(h.server):
        ps=pawn.player_state
        if valid(ps) and ps.player_id in original_positions:
            pawn.set_actor_transform(original_positions[ps.player_id],False,True)
    for flare in list(ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['flare'])):
        if flare.get_name() in state.get('created_flares',[]):flare.destroy_actor()
h.cleanup.append(cleanup_fixture)

def finish(passed,error=None):
    result=old_finish(passed,error)
    if result:
        result.update({'case':case,'ghost_samples':state['samples'],
            'physical_devices_tested':False,'packet_emulation_tested':False,
            'full_mission_acceptance':False,'fresh_lobby_isolation':True,
            'pie_state_left_modified':'Intentional health/pawn-destruction fixtures are not undone; parent must Stop PIE after each case.',
            'target_fields_not_written':True,'scaling_stock_health_not_overridden':True,
            'deadline_decreased':state['deadline_decreased']})
        h.report.write_text(json.dumps(result,indent=2))
    return result
h.finish=finish

def audit_check(name,details=None):
    # Destroyed-pawn fixtures temporarily create pawnless/vanishing peer entries;
    # do not let the generic full-roster snapshot become the test's failure.
    snapshots=[]
    for world in h.worlds:
        players=[]
        for pawn in h.pawns(world):
            if not valid(pawn) or not valid(pawn.player_state):continue
            health=pawn.get_component_by_class(h.classes['health'])
            players.append({'id':pawn.player_state.player_id,'dead':bool(health.get_editor_property('bDead')) if valid(health) else None,'position':str(pawn.get_actor_location())})
        snapshots.append({'world':world.get_name(),'players':players})
    h.checks.append({'name':name,'details':details,'snapshot':snapshots})
h.check=audit_check

def spawn_ghost(position):
    lib=ue.load_object(None,'/Script/Engine.Default__GameplayStatics')
    transform=ue.Transform(location=position)
    ghost=lib.call_method('BeginDeferredActorSpawnFromClass',args=(h.server,GHOST,transform,ue.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,ue.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
    assert ghost
    ghost=lib.call_method('FinishSpawningActor',args=(ghost,transform,ue.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
    assert ghost
    state['ghost']=ghost
    h.fixtures.append({'kind':'PIE-only server ghost spawn','position':str(position),'production_asset_modified':False})
    return ghost

def sample():
    ghost=state.get('ghost')
    if not valid(ghost):return
    now=ue.GameplayStatics.get_time_seconds(h.server)
    target=ghost.get_editor_property('Target')
    until=float(ghost.get_editor_property('BackoffUntil'))
    record={'phase':h.phase,'elapsed':h.elapsed(),'server_local_time':now,
        'position':str(ghost.get_actor_location()),'target':label(target),
        'target_valid':valid(target),'target_living':living_target(target),
        'backoff_until':until,'light_until':float(ghost.get_editor_property('LightUntil'))}
    flare=state.get('flare')
    if valid(flare):record['flare_distance_cm']=(ghost.get_actor_location()-flare.get_actor_location()).length()
    previous=state.get('last_sample')
    if previous and previous['backoff_until']>now+.25 and until<previous['backoff_until']-.002:
        state['deadline_decreased']=True
        record['shortened_from']=previous['backoff_until']
    state['last_sample']=record
    # Keep bounded evidence while retaining every observed deadline regression.
    if not state['samples'] or record.get('shortened_from') or now-state['samples'][-1]['server_local_time']>.08:
        state['samples'].append(record)

def kill(player_id):
    pawn=h.pawn(h.server,player_id)
    ue.GameplayStatics.apply_damage(pawn,1000,None,state['ghost'],None)
    h.fixtures.append({'kind':'server lethal ApplyDamage fixture','player_id':player_id,'purpose':case})
    assert h.prop(pawn,'health','bDead'), 'Lethal fixture did not reach actual health/death graph'

def tick(_delta):
    elapsed=h.elapsed();ghost=state.get('ghost')
    if h.phase=='warmup':
        for i in h.ids:
            if h.prop(h.locals[i],'view','bHeadlampOn'):h.hold(i,'lamp')
            if i==pid:h.fixture_place(i,[-700,-250,95])
            else:h.fixture_place(i,[-1500,200+100*h.ids.index(i),95])
        h.transition('lamps_off')
    elif h.phase=='lamps_off':
        if elapsed>.15:
            for i in h.ids:h.release(i,'lamp')
        if elapsed>.8:
            assert all(not h.prop(h.pawn(h.server,i),'view','bHeadlampOn') for i in h.ids)
            owner=h.pawn(h.server,pid)
            spawn_ghost(owner.get_actor_location()+ue.Vector(1000,0,25))
            h.transition('baseline_target')
    elif h.phase=='baseline_target':
        sample()
        if elapsed>.65:
            assert ghost.get_editor_property('Target')==h.pawn(h.server,pid), 'Fixture owner was not selected naturally'
            for w in h.worlds:
                peers=ue.GameplayStatics.get_all_actors_of_class(w,GHOST)
                assert len(peers)==1, ('Expected sole temporary ghost on every peer',w.get_name(),len(peers))
                assert (peers[0].get_actor_location()-ghost.get_actor_location()).length()<140, 'Ghost position replication did not reach every peer'
            h.check('Natural UpdateTarget chooses nearest living owner and ghost movement reaches every peer')
            if case=='retarget_death':
                kill(pid);h.transition('death_retarget')
            elif case=='all_dead':
                for i in h.ids:kill(i)
                h.transition('no_living_target')
            elif case=='destroyed_target':
                victim=h.pawn(h.server,pid)
                h.fixtures.append({'kind':'destroy targeted server pawn fixture','player_id':pid,'actual_network_logout':False})
                victim.destroy_actor()
                h.transition('destroyed_retarget')
            elif case=='flare_all_safe':
                h.locals[pid].get_controller().set_control_rotation(ue.Rotator(pitch=-90,yaw=0))
                h.hold(pid,'flare');state['stock_before']=h.prop(h.pawn(h.server,pid),'tools','FlaresLeft')
                h.transition('throw_safe_flare')
            else:
                # Approach-only fixture puts real lamp acquisition inside its range.
                ghost.set_actor_location(h.pawn(h.server,pid).get_actor_location()+ue.Vector(320,0,25),False,True)
                h.fixtures.append({'kind':'server ghost initial headlamp approach','distance_cm':320})
                h.aims[pid]=ghost;h.hold(pid,'lamp');h.transition('acquire_lamp')
    elif h.phase in ('death_retarget','destroyed_retarget'):
        sample()
        if elapsed>.7:
            target=ghost.get_editor_property('Target')
            assert living_target(target), 'Ghost failed to pick another living pawn after death/destruction'
            assert target.player_state.player_id!=pid
            h.check('Natural ghost timer retargets after '+('lethal death' if case=='retarget_death' else 'target pawn destruction'))
            h.finish(True)
    elif h.phase=='no_living_target':
        sample()
        if elapsed>.7 and 'empty_at' not in state:
            assert not valid(ghost.get_editor_property('Target')), 'All-dead roster retained a target'
            state['empty_at']=ghost.get_actor_location();h.check('All-dead roster naturally clears the ghost target')
        if elapsed>1.6:
            assert not valid(ghost.get_editor_property('Target'))
            assert (ghost.get_actor_location()-state['empty_at']).length()<5, 'Targetless ghost moves after all targets die'
            h.check('Targetless ghost remains stationary; parent must verify matching Output Log interval is clean')
            h.finish(True)
    elif h.phase=='throw_safe_flare':
        sample()
        if elapsed>.18:h.release(pid,'flare')
        if elapsed>1.5:
            flares=list(ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['flare']))
            assert len(flares)==1 and flares[0].get_owner()==h.pawn(h.server,pid), 'Owning Q did not produce one server flare'
            flare=flares[0];state['flare']=flare;state['created_flares']=[flare.get_name()]
            assert h.prop(h.pawn(h.server,pid),'tools','FlaresLeft')==state['stock_before']-1
            pos=flare.get_actor_location()
            for i in h.ids:
                angle=2*math.pi*h.ids.index(i)/len(h.ids)
                h.fixture_place(i,[pos.x+100*math.cos(angle),pos.y+100*math.sin(angle),95])
            ghost.set_actor_location(pos+ue.Vector(1000,0,75),False,True)
            h.fixtures.append({'kind':'all living pawns inside genuine Q-flare safety; ghost outside glow','flare':flare.get_name()})
            h.transition('all_flare_safe')
    elif h.phase=='all_flare_safe':
        sample()
        if elapsed>.7 and 'safe_start' not in state:
            assert not valid(ghost.get_editor_property('Target')), 'All flare-protected survivors retained a target'
            state['safe_start']=ghost.get_actor_location()
        if elapsed>1.5:
            assert not valid(ghost.get_editor_property('Target'))
            assert (ghost.get_actor_location()-state['safe_start']).length()<10
            h.check('Owning Q and actual flare safety clear every living target without ghost drift')
            pos=state['flare'].get_actor_location();h.fixture_place(pid,[pos.x+650,pos.y,95]);h.transition('leave_glow')
    elif h.phase=='leave_glow':
        sample()
        if elapsed>.65:
            assert ghost.get_editor_property('Target')==h.pawn(h.server,pid), 'Leaving real flare glow did not restore chase'
            h.check('Natural retargeting resumes on the first living owner outside flare glow')
            h.finish(True)
    elif h.phase=='acquire_lamp':
        sample()
        if elapsed>.18:h.release(pid,'lamp')
        now=ue.GameplayStatics.get_time_seconds(h.server)
        if elapsed>.5 and ghost.get_editor_property('BackoffUntil')>now+.3:
            h.check('Actual owning F establishes a longer headlamp backoff deadline')
            h.aims.pop(pid,None);h.locals[pid].get_controller().set_control_rotation(ue.Rotator(pitch=-90,yaw=0))
            h.hold(pid,'flare');h.transition('throw_overlap_flare')
        assert elapsed<6,'Headlamp never acquired fixture ghost with a longer deadline'
    elif h.phase=='throw_overlap_flare':
        sample()
        if elapsed>.18:
            h.release(pid,'flare');h.aims[pid]=ghost
        flares=list(ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['flare']))
        if flares:
            assert len(flares)==1
            state['flare']=flares[0];state['created_flares']=[flares[0].get_name()]
            # One disclosed approach fixture ensures the overlap is exercised.
            if not state.get('overlap_placed'):
                pos=flares[0].get_actor_location();ghost.set_actor_location(pos+ue.Vector(300,0,70),False,True)
                h.fixtures.append({'kind':'ghost/flare overlap initial approach','distance_cm':308})
                state['overlap_placed']=True
        if elapsed>1.5:
            assert state.get('overlap_placed'),'Owning Q prerequisite failed'
            assert not state['deadline_decreased'],'Flare shortened an already-future headlamp/contact backoff deadline; see ghost_samples.shortened_from'
            h.check('Overlapping genuine Q flare and owning F never shorten an existing longer backoff deadline')
            h.finish(True)
RESULT=h.register(tick)
