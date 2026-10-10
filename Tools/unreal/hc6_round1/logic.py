import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import importlib,build
importlib.reload(build)
from build import *
guard()
PLAY='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")'
CLEAR='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2")'
LOBBY='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")'
GS='(Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))'
GM='(Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))'
GET=lambda n:f'(Variables|Default|Get{n})'
SET=lambda n,v:f'(Variables|Default|Set{n} {v})'
STATE='(bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))'
assets={n:unreal.load_asset('/Game/Puzzles/'+n) for n in ACTORS}
for bp in assets.values():
    compile_bp(bp)
    assert any(str(e.name)=='ResetForRound' for e in BP.list_events(bp)),bp.get_name()
    BP.add_event(bp,'ResetForRound')
    BP.get_default_object(bp).get_editor_property('primary_actor_tick').set_editor_property('tick_interval',.1)

p=assets['BP_PressurePlate']
write(p,'ApplyVisual',f'''(fn ApplyVisual ()
 (Components|StaticMesh|SetStaticMesh :self {GET('PlateTop')} :NewMesh {GET('PlateMesh')})
 (Transformation|SetRelativeLocation :self {GET('PlateTop')} :NewLocation
   (Math|Vector|MakeVector :Z (select {GET('Pressed')} 2.0 9.0)))
 (Rendering|SetVisibility :self {GET('PlateTop')} :bNewVisibility {GET('Enabled')})
 (bind material (select {GET('Pressed')} {GET('PressedMaterial')} {GET('ReleasedMaterial')}))
 (Utilities|IsValid :InputObject material
   (:"Is Valid" (Rendering|Material|SetMaterial :self {GET('PlateTop')} :ElementIndex 0 :Material material)) (:"Is Not Valid")))''')
write(p,'Refresh',f'''(fn Refresh ()
 (if (Networking|HasAuthority)
   {SET('OccupantCount','0')}
   (if {GET('Enabled')}
     (for occupant (Collision|GetOverlappingActors :self self)
       (if (Actor|ActorHasTag :self occupant :Tag "HC_PlateWeight")
         {SET('OccupantCount',f'(+ {GET("OccupantCount")} 1)')}
         (else
           (bind pawn (Utilities|Casting|CastToPawn :Object occupant)
             (:then {SET('OccupantCount',f'(+ {GET("OccupantCount")} 1)')}) (:CastFailed))))))
   {SET('Pressed',f'(and {GET("Enabled")} (> {GET("OccupantCount")} 0))')}))''')
write(p,'SetEnabled',f'''(fn SetEnabled (Value)
 (if (Networking|HasAuthority) {SET('Enabled','Value')} (CallFunction|Refresh)))''')
write(p,'ResetActor',f'''(fn ResetActor ()
 (if (Networking|HasAuthority) {SET('Enabled','false')} {SET('Pressed','false')} {SET('OccupantCount','0')}))''')
write(p,'Initialize','(fn Initialize () (CallFunction|ApplyVisual))')
for n in ('Pressed','Enabled'):write(p,'OnRep_'+n,f'(fn OnRep_{n} () (CallFunction|ApplyVisual))')

g=assets['BP_ChamberGate']
write(g,'ApplyVisual',f'''(fn ApplyVisual ()
 (Components|StaticMesh|SetStaticMesh :self {GET('GateLeaf')} :NewMesh {GET('GateMesh')})
 (Transformation|SetRelativeLocation :self {GET('GateLeaf')} :NewLocation
   (Math|Vector|MakeVector :Z (select {GET('Open')} {GET('OpenHeight')} 0.0))))''')
write(g,'Refresh',f'''(fn Refresh ()
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   {SET('Open',f'(or (> index {GET("RoundIndex")}) (and (== index {GET("RoundIndex")}) (Utilities|Enum|Equal(Enum) :A phase :B {CLEAR})))')}) (:CastFailed))))''')
write(g,'Initialize','(fn Initialize () (CallFunction|ApplyVisual) (CallFunction|Refresh))')
write(g,'ResetActor',f'(fn ResetActor () (if (Networking|HasAuthority) {SET("Open","false")}))')
write(g,'OnRep_Open','(fn OnRep_Open () (CallFunction|ApplyVisual))')

pad=assets['BP_StartPad']
variable(pad,'EveryonePresent','bool',False)
variable(pad,'HoldingStates',unreal.PlayerState.static_class(),array=True)
write(pad,'ApplyVisual','(fn ApplyVisual ())')
write(pad,'Initialize','(fn Initialize () (CallFunction|ResetActor))')
write(pad,'ResetActor',f'''(fn ResetActor () (if (Networking|HasAuthority)
 {SET('HoldStarted','-1.0')} {SET('Started','false')} {SET('EveryonePresent','false')}
 (Utilities|Array|Clear :TargetArray {GET('PresentStates')})
 (Utilities|Array|Clear :TargetArray {GET('HoldingStates')})))''')
write(pad,'Refresh',f'''(fn Refresh ()
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (Utilities|Enum|Equal(Enum) :A phase :B {LOBBY}) (not {GET('Started')}))
    (Utilities|Array|Clear :TargetArray {GET('PresentStates')})
    (for actor (Collision|GetOverlappingActors :self self)
     (bind pawn (Utilities|Casting|CastToPawn :Object actor)
      (:then (bind ps (Class|Pawn|GetPlayerState :self pawn))
       (Utilities|IsValid :InputObject ps
        (:"Is Valid" (Utilities|Array|AddUnique :TargetArray {GET('PresentStates')} :NewItem ps)) (:"Is Not Valid"))) (:CastFailed)))
    (bind players (Class|GameStateBase|GetPlayerArray :self gs))
    (if (!= (Utilities|Array|Length {GET('HoldingStates')}) (Utilities|Array|Length players)) {SET('HoldStarted','-1.0')})
    (for ps players
     (if (not (Utilities|Array|ContainsItem :TargetArray {GET('HoldingStates')} :ItemToFind ps)) {SET('HoldStarted','-1.0')}))
    {SET('ExpectedCount','(Utilities|Array|Length players)')}
    {SET('InsideCount',f'(Utilities|Array|Length {GET("PresentStates")})')}
    {SET('EveryonePresent',f'(and (>= {GET("ExpectedCount")} 2) (<= {GET("ExpectedCount")} 4))')}
    (for ps players (if (not (Utilities|Array|ContainsItem :TargetArray {GET('PresentStates')} :ItemToFind ps)) {SET('EveryonePresent','false')}))
    (if {GET('EveryonePresent')}
     (bind now (GameState|GetServerWorldTimeSeconds :self gs))
     (if (< {GET('HoldStarted')} 0.0)
      (Utilities|Array|Clear :TargetArray {GET('HoldingStates')})
      (for ps players (Utilities|Array|AddUnique :TargetArray {GET('HoldingStates')} :NewItem ps))
      {SET('HoldStarted','now')})
     (if (>= (- now {GET('HoldStarted')}) {GET('HoldSeconds')})
      (bind gm {GM} (:then {SET('Started','true')}
       (Class|BPCoopGameMode|StartRound :self gm :Index 1)) (:CastFailed)))
     (else {SET('HoldStarted','-1.0')}))
    (else {SET('HoldStarted','-1.0')}))) (:CastFailed))))''')

s=assets['BP_PuzzleSetup']
variable(s,'ActivePlates',p.generated_class(),array=True)
variable(s,'Slots','int',array=True)
write(s,'ApplyVisual','(fn ApplyVisual ())')
write(s,'RemoveStatues',f'''(fn RemoveStatues ()
 (if (Networking|HasAuthority)
  (for statue {GET('Statues')} (Utilities|IsValid :InputObject statue
   (:"Is Valid" (Actor|DestroyActor :self statue)) (:"Is Not Valid")))
  (Utilities|Array|Clear :TargetArray {GET('Statues')})))''')
write(s,'ResetActor',f'''(fn ResetActor ()
 (if (Networking|HasAuthority)
  (CallFunction|RemoveStatues) {SET('ConfiguredAttempt','-1')} {SET('Ready','false')}
  (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_PressurePlate.BP_PressurePlate_C")
   (if (Actor|ActorHasTag :self actor :Tag {GET('PuzzleTag')})
    (bind plate (Utilities|Casting|CastToBP_PressurePlate :Object actor)
      (:then (Class|BPPressurePlate|ResetActor :self plate)) (:CastFailed))))))''')
write(s,'Initialize','(fn Initialize () (CallFunction|ResetActor) (CallFunction|Refresh))')
write(s,'Configure',f'''(fn Configure (Attempt)
 (if (Networking|HasAuthority)
  (CallFunction|ResetActor) {SET('ConfiguredAttempt','Attempt')}
  (bind gs {GS} (:then
   (bind data (Utilities|GetDataTableRow :DataTable "/Game/Puzzles/DT_RoundScaling.DT_RoundScaling"
     :RowName (Class|BPCoopGameState|GetScalingRow :self gs))
    (:then
     (bind (plates statues) (Utilities|Struct|BreakSRoundScaling :S_RoundScaling data))
     {SET('PlateCount','plates')} {SET('StatueCount','statues')}
     (Utilities|Array|Clear :TargetArray {GET('ActivePlates')})
     (Utilities|Array|Clear :TargetArray {GET('Slots')})
     (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_PressurePlate.BP_PressurePlate_C")
      (if (Actor|ActorHasTag :self actor :Tag {GET('PuzzleTag')})
       (bind plate (Utilities|Casting|CastToBP_PressurePlate :Object actor)
        (:then (bind slot (Class|BPPressurePlate|GetPlateSlot :self plate))
         (if (and (>= slot 0) (< slot plates))
          (Utilities|Array|Add :TargetArray {GET('ActivePlates')} :NewItem plate)
          (Utilities|Array|AddUnique :TargetArray {GET('Slots')} :NewItem slot)
          (Class|BPPressurePlate|SetEnabled :self plate :Value true))) (:CastFailed))))
     (if (and (and (== (Utilities|Array|Length {GET('ActivePlates')}) plates)
       (== (Utilities|Array|Length {GET('Slots')}) plates))
       (and (>= (Utilities|Array|Length {GET('StatueTransforms')}) statues)
        (Utilities|IsValidClass :Class {GET('StatueClass')})))
      (for i (range statues)
       (bind spawned (Game|SpawnActorfromClass :Class {GET('StatueClass')}
         :SpawnTransform (Utilities|Array|Get(acopy) {GET('StatueTransforms')} i)
         :CollisionHandlingOverride "AlwaysSpawn")
         (:then (Utilities|IsValid :InputObject spawned
          (:"Is Valid" (Utilities|Array|Add :TargetArray {GET('Statues')} :NewItem spawned)) (:"Is Not Valid")))))
      {SET('Ready',f'(== (Utilities|Array|Length {GET("Statues")}) statues)')}))
    (:RowNotFound {SET('Ready','false')}))) (:CastFailed))))''')
write(s,'Refresh',f'''(fn Refresh ()
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (== index {GET('RoundIndex')}) (Utilities|Enum|Equal(Enum) :A phase :B {PLAY}))
    (if (!= attempt {GET('ConfiguredAttempt')}) (CallFunction|Configure :Attempt attempt))
    (if {GET('Ready')}
     {SET('PressedCount','0')}
     (for plate {GET('ActivePlates')}
      (Utilities|IsValid :InputObject plate
       (:"Is Valid" (Class|BPPressurePlate|Refresh :self plate)
        (if (Class|BPPressurePlate|GetPressed :self plate) {SET('PressedCount',f'(+ {GET("PressedCount")} 1)')})) (:"Is Not Valid")))
     (if (== {GET('PressedCount')} {GET('PlateCount')})
      (bind gm {GM} (:then (Class|BPCoopGameMode|ClearRound :self gm)) (:CastFailed)))))) (:CastFailed))))''')
for bp in assets.values():
    reset='(CallFunction|ResetActor)'
    write(bp,'EventGraph',f'''(event EventBeginPlay (CallFunction|Initialize))
      (event EventTick (DeltaSeconds) (CallFunction|Refresh))
      (event ResetForRound (Index Attempt)
       (if (and (Networking|HasAuthority) (== Index {GET('RoundIndex')})) {reset}))''')
    compile_bp(bp);unreal.EditorAssetLibrary.save_loaded_asset(bp)
(OUT/'logic-build.json').write_text(json.dumps({n:str(bp.get_editor_property('status')) for n,bp in assets.items()},indent=2))



