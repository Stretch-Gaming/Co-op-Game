"""New SixRound-only lethal chasm trigger; never modifies legacy fall actors."""
import sys,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import authoring;importlib.reload(authoring)
from authoring import *
guard()
bp=create('/Game/Hazards/Traps/SixRound/BP_SixRoundChasmVolume',ue.Actor.static_class())
cdo=BP.get_default_object(bp);cdo.set_editor_property('replicates',True)
zone,_=component(bp,'ChasmZone',ue.BoxComponent)
zone.set_box_extent(ue.Vector(7500,12800,200));zone.set_collision_profile_name('OverlapAllDynamic');zone.set_editor_property('generate_overlap_events',True)
fn(bp,'SRChasmOverlap',inputs=[('OtherActor',ue.Actor.static_class())])
write(bp,'SRChasmOverlap',f'''
 (if (Networking|HasAuthority)
  (bind chasmGS (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (chasmIndex chasmPhase chasmAttempt chasmEnds chasmRow) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self chasmGS)))
    (if (Utilities|Enum|Equal(Enum) chasmPhase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))
     (bind faller (Utilities|Casting|CastToBP_CoopCharacter :Object OtherActor)
      (:then (Game|Damage|ApplyDamage :DamagedActor faller :BaseDamage 10000.0 :DamageCauser self)) (:CastFailed)))) (:CastFailed)))''','OtherActor')
event(bp,'ReceiveActorBeginOverlap','SRChasmOverlap',['OtherActor']);save(bp)
RESULT={'asset':bp.get_path_name(),'legacy_fall_assets_untouched':True,'server_damage_playing_only':True,'damage':10000,'runtime_acceptance_pending':True}
