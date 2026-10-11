"""Genuine owner Q + F; initial ghost spawn/approach fixtures, no ghost writes."""
import json
import sys
import unreal as ue
sys.path.insert(0, str(HERE))
from harness import Harness
h = Harness(ARGS, 'tools-ghost')
pid = h.ids[int(ARGS['owner_ordinal'])]; assert pid in h.ids
owner=h.locals[pid]; pawn=h.pawn(h.server,pid)
ghost_class=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
h.fixture_place(pid,[-500,500,95])
owner.get_controller().set_control_rotation(ue.Rotator(pitch=-90,yaw=0))
h.fixtures.append({'kind':'owning downward aim fixture','owner':pid})
state={'stock':h.prop(pawn,'tools','FlaresLeft')}; assert state['stock']>0
samples=[]
old_finish=h.finish
def finish(passed,error=None):
    result=old_finish(passed,error)
    if result:
        result['ghost_samples']=samples
        h.report.write_text(json.dumps(result,indent=2))
    return result
h.finish=finish
def spawn_ghost(position):
    library=ue.load_object(None,'/Script/Engine.Default__GameplayStatics')
    actor=library.call_method('BeginDeferredActorSpawnFromClass',args=(h.server,ghost_class,ue.Transform(location=position),ue.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,ue.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
    assert actor
    actor=library.call_method('FinishSpawningActor',args=(actor,ue.Transform(location=position),ue.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
    h.fixtures.append({'kind':'PIE-only ghost initial spawn','position':str(position),'saved_packages_modified':False})
    h.cleanup.append(lambda: actor.destroy_actor() if ue.SystemLibrary.is_valid(actor) else None)
    return actor
def tick(_delta):
    elapsed=h.elapsed()
    if h.phase=='warmup':
        owner.get_controller().set_control_rotation(ue.Rotator(pitch=-90,yaw=0))
        if elapsed>1:
            if h.prop(owner,'view','bHeadlampOn'):h.hold(pid,'lamp')
            h.transition('lamp_off')
    elif h.phase=='lamp_off':
        if elapsed>.2:h.release(pid,'lamp')
        if elapsed>1:
            for other in h.ids:
                if other!=pid:h.fixture_place(other,[-900,500,95])
            ghost=spawn_ghost(pawn.get_actor_location()+ue.Vector(900,0,20))
            state['normal_ghost']=ghost;state['normal_position']=ghost.get_actor_location()
            h.transition('normal_chase')
    elif h.phase=='normal_chase' and elapsed>3:
        ghost=state['normal_ghost'];travel=(ghost.get_actor_location()-state['normal_position']).length()
        assert travel>100,('Normal ghost movement too slow',travel,ghost.get_editor_property('GhostSpeed'))
        peers=list(ue.GameplayStatics.get_all_actors_of_class(owner.get_world(),ghost_class))
        assert len(peers)==1,('Expected the sole fixture ghost on owning peer',len(peers),ghost.get_name())
        peer=peers[0]
        assert (peer.get_actor_location()-ghost.get_actor_location()).length()<100,'Owning peer ghost movement did not replicate'
        h.check('normal unlit ghost chases at scaled speed and movement reaches owner peer',{'distance_cm':travel,'speed':ghost.get_editor_property('GhostSpeed'),'damage':ghost.get_editor_property('GhostDamage')})
        ghost.destroy_actor();h.hold(pid,'flare');h.transition('throw')
    elif h.phase=='throw':
        if elapsed>.2:h.release(pid,'flare')
        if elapsed>2:
            flares=[a for a in ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['flare']) if a.get_owner()==pawn]
            assert len(flares)==1
            flare=flares[0];state['flare']=flare;state['start']=flare.get_editor_property('BurnStarted')
            ghost=spawn_ghost(flare.get_actor_location()+ue.Vector(400,0,60));state['ghost']=ghost
            samples.append({'age':ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds()-state['start'],'ghost_speed':ghost.get_editor_property('GhostSpeed'),'ghost_damage':ghost.get_editor_property('GhostDamage'),'scope':'unchanged ApplyScaling read-only observation'})
            assert ghost.call_method('IsInFlareGlow',args=(pawn,))
            h.check('native burning flare marks owner safe through unchanged ghost query')
            h.transition('flare_avoid')
    elif h.phase=='flare_avoid':
        ghost=state['ghost'];flare=state['flare']
        age=ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds()-state['start']
        if ue.SystemLibrary.is_valid(flare):
            distance=(ghost.get_actor_location()-flare.get_actor_location()).length()
            if elapsed>.8:assert distance>=440, ('Ghost remains in flare glow',distance)
            if elapsed>1 and 'avoidance' not in state:
                state['avoidance']=True
                h.check('unchanged ghost repels from real flare glow',{'distance_cm':distance})
            if not samples or age-samples[-1]['age']>1:
                samples.append({'age':age,'distance_cm':distance,'owner_safe':bool(ghost.call_method('IsInFlareGlow',args=(pawn,))),'target':str(ghost.get_editor_property('Target'))})
        if age>21:
            assert not ue.SystemLibrary.is_valid(flare)
            assert not ghost.call_method('IsInFlareGlow',args=(pawn,))
            h.check('native flare expiry removes ghost safe-zone query')
            # Initial headlamp scenario reposition is explicitly a fixture.
            position=pawn.get_actor_location()+ue.Vector(500,0,20)
            ghost.set_actor_location(position,False,True)
            h.fixtures.append({'kind':'PIE-only headlamp initial ghost approach','position':str(position)})
            h.aims[pid]=ghost
            h.hold(pid,'lamp');h.transition('headlamp')
    elif h.phase=='headlamp':
        if elapsed>.2:h.release(pid,'lamp')
        ghost=state['ghost'];now=ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds()
        until=ghost.get_editor_property('LightUntil')
        distance=(ghost.get_actor_location()-pawn.get_actor_location()).length()
        samples.append({'headlamp_elapsed':elapsed,'distance_cm':distance,'light_until':until,'server_now':now,'backoff_until':ghost.get_editor_property('BackoffUntil')})
        if until>now and 'lamp_first' not in state:
            state['lamp_first']=(elapsed,distance)
        if 'lamp_first' in state and elapsed-state['lamp_first'][0]>.5:
            assert until>now,('Aimed headlamp stopped repelling ghost',until,now)
            gain=distance-state['lamp_first'][1]
            assert gain>20,('Ghost did not move away after lamp acquired it',gain)
            h.check('owning headlamp triggers unchanged server ghost backoff',{'distance_cm':distance,'distance_gain_after_acquisition_cm':gain,'light_until':until,'server_now':now})
            h.finish(True)
        assert elapsed<8,'Headlamp never acquired and repelled the ghost'
RESULT=h.register(tick)
