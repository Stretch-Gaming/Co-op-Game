"""Tool restrictions with native pickup/Q/F; disclosed damage/round fixtures."""
import sys
import unreal as ue
sys.path.insert(0,str(HERE))
from harness import Harness
h=Harness(ARGS,'tools-restrictions-'+ARGS['case'])
pid=h.ids[int(ARGS['owner_ordinal'])];assert pid in h.ids
pawn=h.pawn(h.server,pid);owner=h.locals[pid];case=ARGS['case']
state={'stock':h.prop(pawn,'tools','FlaresLeft'),'lamp':h.prop(pawn,'view','bHeadlampOn')}
assert h.round()['phase'] in (0,1)
if case=='heavy':
    if h.round()['phase']==0:
        ue.GameplayStatics.get_game_mode(h.server).call_method('StartRound',args=(1,))
        h.fixtures.append({'kind':'server GameMode StartRound(1) setup fixture','natural_start_pad_transaction_proven':False})
elif case=='dead':
    ue.GameplayStatics.apply_damage(pawn,9999,None,None,None)
    h.fixtures.append({'kind':'lethal ApplyDamage fixture through production health event','owner':pid,'round':h.round(),'regroup_lifecycle_proven':False})
    h.transition('dead')
else:raise AssertionError(case)
def tick(_delta):
    elapsed=h.elapsed()
    if h.phase=='warmup' and elapsed>1:
        statues=list(ue.GameplayStatics.get_all_actors_of_class(h.server,ue.load_asset('/Game/Puzzles/BP_Statue').generated_class()))
        assert statues,'Real puzzle statues must exist after Round1 starts'
        state['item']=statues[0]
        h.focus(pid,state['item']);h.transition('focus')
    elif h.phase=='focus' and elapsed>1:
        assert h.focused(pid,state['item'])
        h.hold(pid,'interact');h.transition('pickup')
    elif h.phase=='pickup':
        if elapsed>.2:h.release(pid,'interact')
        if elapsed>1:
            assert h.prop(pawn,'carry','CarriedItem')==state['item']
            assert pawn.call_method('IsCarryingHeavy')
            h.aims.clear();h.hold(pid,'flare');h.hold(pid,'lamp');h.transition('guards')
    elif h.phase=='dead' and elapsed>1:
        assert h.prop(pawn,'health','bDead')
        h.hold(pid,'flare');h.hold(pid,'lamp');h.transition('guards')
    elif h.phase=='guards':
        if elapsed>.2:h.release(pid,'flare');h.release(pid,'lamp')
        if elapsed>1.5:
            for world in h.worlds:
                peer=h.pawn(world,pid)
                assert h.prop(peer,'tools','FlaresLeft')==state['stock']
                if case=='heavy':assert h.prop(peer,'view','bHeadlampOn')!=state['lamp'],'Heavy carrier retains working headlamp'
            assert not h.comp(pawn,'tools').call_method('CanUseTools')
            assert not [a for a in ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['flare']) if a.get_owner()==pawn]
            h.check('native Q blocked with stock unchanged while '+case,{'owner':pid,'headlamp_works_while_heavy':case=='heavy'})
            if case=='heavy':h.hold(pid,'drop');h.transition('drop')
            else:h.finish(True)
    elif h.phase=='drop':
        if elapsed>.2:h.release(pid,'drop')
        if elapsed>1:
            assert h.prop(pawn,'carry','CarriedItem') is None
            h.check('native Drop ends heavy carry');h.finish(True)
RESULT=h.register(tick)
