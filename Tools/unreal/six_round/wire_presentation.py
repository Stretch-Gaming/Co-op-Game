"""Use each taking style once and alternate ghost/cave-being escape members."""
import sys
sys.path.insert(0,str(HERE))
from authoring import *
guard()
taking=ue.load_asset('/Game/Player/Taking/BP_TakingDirector')
graph=BP.get_graph(taking,'TakePlayer')
setter=next(n for n in BP.find_nodes(graph) if n.get_class().get_name()=='K2Node_VariableSet' and BP._get_node_info(n).type_id.endswith('ScareStyle'))
execute=setter.find_execute_pin();prior=list(execute.list_connected_pins());assert len(prior)==1
call=BP.create_node(graph,'CallFunction|NextPresentationStyle',ue.IntPoint(1600,1000),declaring_class=taking.generated_class())
for pin in prior:execute.break_single_pin_link(pin);assert pin.try_create_connection(call.find_execute_pin())
assert call.find_then_pin().try_create_connection(execute)
value=setter.find_input_pin('ScareStyle')
for pin in list(value.list_connected_pins()):value.break_single_pin_link(pin)
assert call.find_output_pin('Style').try_create_connection(value)
save(taking)
chase=ue.load_asset('/Game/Player/Ghosts/BP_ChaseDirector')
fn(chase,'SpawnGhostWaveMember',[('Location','Vector')])
write(chase,'SpawnGhostWaveMember',f'''
 (if (Networking|HasAuthority)
  (bind spawned (Game|SpawnActorfromClass :Class "/Game/Player/Ghosts/BP_Ghost.BP_Ghost_C" :SpawnTransform (Math|Transform|MakeTransform :Location Location) :CollisionHandlingOverride "AlwaysSpawn")
   (:then (Actor|SetLifeSpan :self spawned :InLifespan 45.0) (Utilities|Array|Add :TargetArray {V('WaveGhosts')} :NewItem spawned))))''','Location')
write(chase,'SpawnWave',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind row (Class|BPCoopGameState|GetScalingRow :self gs))
    {S('WaveSize','(select (== row "2") 2 (select (== row "3") 3 (select (== row "4") 4 0)))')}
    (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
     (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object actor)
      (:then (bind carrying (Class|BPCoopCharacter|GetCarryingRelic :self pawn))
       (if carrying
        (for i (range {V('WaveSize')})
         (bind position (+ (Transformation|GetActorLocation :self pawn) (Utilities|Struct|MakeVector :X (select (== i 0) -1500.0 1500.0) :Y (* i 250.0) :Z 100.0)))
         (if (or (== i 1) (== i 3))
          (CallFunction|SpawnCaveBeingWaveMember :Location position)
          (else (CallFunction|SpawnGhostWaveMember :Location position)))))) (:CastFailed)))
    {S('WaveNumber',f'(+ {V("WaveNumber")} 1)')}
    {S('LastWaveAt','(GameState|GetServerWorldTimeSeconds :self gs)')}) (:CastFailed)))''')
save(chase)
RESULT={'distinct_taking_styles':True,'escape_wave_species':'alternating ghost/cave being, counts/timing unchanged','runtime_pending':True}
