import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
bp=ue.load_asset('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD')
body='''
 (bind size (UserInterface|Geometry|GetLocalSize :Geometry (Widget|GetCachedGeometry)))
 (bind (width height) (Math|Vector2D|BreakVector2D :InVec size))
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then
   (bind area (Class|BPCoopGameState|GetAreaName :self gs))
   (if (not (Utilities|String|EqualExactly(String) :A area :B "Egypt"))
    (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (bind cave (Utilities|String|EqualExactly(String) :A area :B "Cave"))
    (bind playing (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")))
    (bind title (select cave (Utilities|String|BuildString(Integer) :Prefix "CAVE  -  CHAMBER " :InInt index :Suffix " / 3") "THE MAZE"))
    (bind instruction (select cave (select (== index 0) "Stand together on the start pad." (select playing (select (== index 1) "Use statues and teammates to press the plates." (select (== index 2) "Carry the heavy key to the altar." "Hold the gate lever. Reach the far switch.")) "The way is open. Meet in the next chamber.")) "Find the relic chamber. Brace to boost a teammate."))
    (bind score (Utilities|String|BuildString(Integer) :Prefix "RELICS  " :InInt (Class|BPCoopGameState|GetRelicsCollected :self gs) :Suffix " / "))
    (bind total (Utilities|String|BuildString(Integer) :AppendTo score :InInt (Class|BPCoopGameState|GetRelicsAvailable :self gs)))
'''
for text,x,y,size in [('title','24','20',20),('total','24','50',18),('instruction','24','82',15)]:
 body+=f'(Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) {text}) :Position (Math|Vector2D|MakeVector2D :X {x}.0 :Y {y}.0) :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize {size} :Tint "(R=0.93,G=0.82,B=0.55,A=1)")\n'
body+='\n    (bind pc (Widget|GetOwningPlayer))\n    (bind controls (select (Game|Player|IsPrimaryPlayer :self pc) "E use | Space jump | Shift brace | V view | F light | F5 teammate" "Arrows move | / jump | Enter use | R Shift brace | C view | H light"))\n    (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) controls) :Position (Math|Vector2D|MakeVector2D :X 24.0 :Y (- height 40.0)) :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize 12 :Tint "(R=0.93,G=0.82,B=0.55,A=1)")\n    (bind player (Controller|GetControlledPawn :self pc))\n    (Utilities|IsValid :InputObject player\n     (:"Is Valid"\n      (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self player :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))\n       (:then\n        (bind downed (Class|ACHealth|IsDowned :self health))\n        (bind hp (Utilities|String|BuildString(Integer) :Prefix "HEALTH " :InInt (Math|Float|Truncate :A (Class|ACHealth|GetHealth :self health))))\n        (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) (select downed "DOWNED - a teammate can hold E to revive you" hp)) :Position (Math|Vector2D|MakeVector2D :X 24.0 :Y (- height 68.0)) :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize 16 :Tint "(R=0.93,G=0.82,B=0.55,A=1)")) (:CastFailed))) (:"Is Not Valid")))) (:CastFailed))\n'
write(bp,'OnPaint',body,'Context');save(bp)
RESULT={'area_round_health_and_relics':True,'per_player_controls':True,'runtime_visual_acceptance_pending':True}

