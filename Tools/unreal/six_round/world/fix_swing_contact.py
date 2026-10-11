"""Narrow editor patch: only the SixRound parent's swing contact and reset hooks.

The primary runs this after PIE ends. No level, child defaults, spike/dart graph,
shared health or hazard table writes. Native contact/noncontact QA remains required.
"""
import sys,importlib,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import authoring;importlib.reload(authoring)
from authoring import *

PATH='/Game/Hazards/Traps/SixRound/BP_SixRoundTrap'

def append_hook(bp,name,handler):
    raw=BP.read_graph_dsl(BP.get_graph(bp,name))
    match=re.match(r'^\s*\(fn\s+'+re.escape(name)+r'\s+\([^)]*\)([\s\S]*)\)\s*$',raw)
    assert match,'Unexpected native function DSL header: '+name
    body=match.group(1);hook='(CallFunction|'+handler+')'
    if hook not in body:write(bp,name,body+'\n'+hook)

def apply_swing_contact(bp):
    assert bp.get_path_name().split('.')[0]==PATH
    var(bp,'SwingHitActors',ue.Actor.static_class(),array=True)
    var(bp,'LastSwingCycle','int',-1)
    for name in ('SRTrapConfigureSwingContact','SRTrapResetSwingContact','SRTrapProcessSwing'):fn(bp,name)
    beam,_=component(bp,'TrapBeam',ue.StaticMeshComponent)
    pawn_channel=next(getattr(ue.CollisionChannel,name) for name in ('PAWN','ECC_PAWN') if hasattr(ue.CollisionChannel,name))
    response_enum=getattr(ue,'CollisionResponseType',ue.CollisionResponse)
    ignore_response=next(getattr(response_enum,n) for n in ('ECR_IGNORE','IGNORE') if hasattr(response_enum,n))
    overlap_response=next(getattr(response_enum,n) for n in ('ECR_OVERLAP','OVERLAP') if hasattr(response_enum,n))
    beam.set_collision_response_to_all_channels(ignore_response)
    beam.set_collision_response_to_channel(pawn_channel,overlap_response)
    beam.set_editor_property('generate_overlap_events',True)
    # Default Kind0 remains noncolliding. Runtime configuration also covers
    # already placed child instances and their inherited component templates.
    beam.set_collision_profile_name('NoCollision')
    write(bp,'SRTrapConfigureSwingContact',f'''
 (Collision|SetCollisionResponseToAllChannels :self {V('TrapBeam')} :NewResponse "ECR_Ignore")
 (Collision|SetCollisionResponseToChannel :self {V('TrapBeam')} :Channel "ECC_Pawn" :NewResponse "ECR_Overlap")
 (Collision|SetGenerateOverlapEvents :self {V('TrapBeam')} :bGenerateOverlapEvents true)
 (if (== {V('Kind')} 2)
  (Collision|SetCollisionEnabled :self {V('TrapBeam')} :NewType "QueryOnly")
  (else (Collision|SetCollisionEnabled :self {V('TrapBeam')} :NewType "NoCollision")))''')
    write(bp,'SRTrapResetSwingContact',f'''(if (Networking|HasAuthority)
 (Utilities|Array|Clear :TargetArray {V('SwingHitActors')}) {S('LastSwingCycle','-1')})''')
    write(bp,'SRTrapProcessSwing',f'''
 (if (and (Networking|HasAuthority) (and (== {V('Kind')} 2) (>= {V('Now')} {V('StartTime')})))
  (bind contactGS (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (contactIndex contactPhase contactAttempt contactEnds contactRow) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self contactGS)))
    (if (Utilities|Enum|Equal(Enum) contactPhase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))
     (bind contactCycle (Math|Float|Floor :A (/ (* (- {V('Now')} {V('StartTime')}) {V('SwingSpeed')}) 3.14159)))
     (if (!= contactCycle {V('LastSwingCycle')})
      {S('LastSwingCycle','contactCycle')} (Utilities|Array|Clear :TargetArray {V('SwingHitActors')})
      (Audio|PlaySoundatLocation :Sound "/Game/Hazards/Art/Audio/SFX_SwingLog_Whoosh.SFX_SwingLog_Whoosh" :Location (Transformation|GetActorLocation)))
     (for victim (Collision|GetOverlappingActors :self {V('TrapBeam')} :ClassFilter "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
      (if (not (Utilities|Array|ContainsItem :TargetArray {V('SwingHitActors')} :ItemToFind victim))
       (Utilities|Array|AddUnique :TargetArray {V('SwingHitActors')} :NewItem victim)
       (Game|Damage|ApplyDamage :DamagedActor victim :BaseDamage {V('Damage')} :DamageCauser self))))) (:CastFailed)))''')
    append_hook(bp,'SRTrapApplyTrapVisual','SRTrapConfigureSwingContact')
    append_hook(bp,'SRTrapBeginTrap','SRTrapConfigureSwingContact')
    append_hook(bp,'SRTrapResetSchedule','SRTrapResetSwingContact')
    save(bp)
    return {'writes':[PATH],'damage_component':'TrapBeam (PrimitiveComponent GetOverlappingActors)','damage_limit':'once per victim per half-cycle, server Playing only, no pre-start damage','collision':'QueryOnly; Pawn overlap; overlap generation on every peer; other trap Kinds NoCollision','runtime_acceptance_pending':True}

if __name__=='__main__':
    guard();bp=ue.load_asset(PATH);assert bp
    RESULT=apply_swing_contact(bp)
