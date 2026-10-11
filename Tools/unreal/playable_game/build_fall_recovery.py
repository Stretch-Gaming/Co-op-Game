import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
fall=create('/Game/Hazards/Traps/BP_FallVolume',ue.TriggerBox.static_class());fn(fall,'RecoverFall',[('OtherActor',ue.Actor.static_class())])
write(fall,'RecoverFall','''
 (if (Networking|HasAuthority)
  (bind player (Utilities|Casting|CastToBP_CoopCharacter :Object OtherActor)
   (:then
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Rounds/BP_RoundDirector.BP_RoundDirector_C")
     (bind director (Utilities|Casting|CastToBP_RoundDirector :Object item)
      (:then
       (bind checkpoint (Utilities|Casting|CastToBP_Checkpoint :Object (Class|BPRoundDirector|GetCurrentCheckpoint :self director)))
       (Utilities|IsValid :InputObject checkpoint
        (:"Is Valid"
         (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self player))
          (:then
           (bind recovered (Class|BPRoundDirector|RecoverPlayer :self director :PlayerPawn player))
           (if recovered
            (bind spot (Class|BPCheckpoint|GetSpawnTransform :self checkpoint :Slot (Class|BPCoopPlayerState|GetColorSlot :self ps)))
            (Transformation|SetActorTransform :self player :NewTransform spot :bSweep false :bTeleport true)
            (Game|Damage|ApplyDamage :DamagedActor player :BaseDamage 50.0 :DamageCauser self))) (:CastFailed))) (:"Is Not Valid"))) (:CastFailed)))) (:CastFailed)))''','OtherActor')
event(fall,'ReceiveActorBeginOverlap','RecoverFall',['OtherActor']);save(fall)
RESULT={'fallers_return_to_checkpoint':True,'fall_damage':50,'runtime_acceptance_pending':True}

