"""Six-round HUD/prompt/results paint only; no owner/input/gameplay changes.
ARGS font_heading/font_body accept primary-imported redistribution-approved Font assets.
Engine fallback is temporary and explicitly fails final presentation readiness.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round'))
from authoring import *
guard();ARGS=globals().get('ARGS',{})
heading=ARGS.get('font_heading','/Game/Shared/UI/Fonts/F_AveriaSerifLibre_Bold.F_AveriaSerifLibre_Bold');bodyfont=ARGS.get('font_body','/Game/Shared/UI/Fonts/F_AveriaSerifLibre_Regular.F_AveriaSerifLibre_Regular')
assert ue.load_asset(heading) and ue.load_asset(bodyfont),'Import the approved Font assets before specifying their paths'
ART='/Game/Puzzles/Art/HCA3_UI/';UI='/Game/Puzzles/UI/SixRound/'
colors={'Shadow':(.118,.141,.2,.7),'Frame':(.29,.275,.322,1),'Plate':(.086,.106,.153,1),'Inner':(.165,.188,.259,1)}
white=ue.load_asset('/Engine/EngineResources/WhiteSquareTexture');assert white,'Engine white square texture required for solid panels'
for name,color in colors.items():
 path=UI+'DA_'+name+'Brush';brush=ue.load_asset(path) or ue.AssetToolsHelpers.get_asset_tools().create_asset('DA_'+name+'Brush',UI.rstrip('/'),ue.SlateBrushAsset,ue.SlateBrushAssetFactory())
 slate=ue.WidgetLibrary.make_brush_from_texture(white,1,1);slate.set_editor_property('tint_color',ue.SlateColor(specified_color=ue.LinearColor(*color)))
 brush.set_editor_property('brush',slate);assert ue.EditorAssetLibrary.save_loaded_asset(brush,False)

def xy(x,y):return f'(Math|Vector2D|MakeVector2D :X {x} :Y {y})'
def mul(v):return f'(* {v} scale)'
def box(brush,x,y,w,h):return f'(Painting|DrawBox :Context Context :Position {xy(x,y)} :Size {xy(w,h)} :Brush "{UI}DA_{brush}Brush.DA_{brush}Brush")'
def panel(x,y,w,h):
 # Opaque plate plus darker inset and existing carved art border; four visible layers.
 return '\n'.join([box('Shadow',f'(+ {x} {mul(3.0)})',f'(+ {y} {mul(4.0)})',w,h),box('Frame',x,y,w,h),f'(Painting|DrawBox :Context Context :Position {xy(x,y)} :Size {xy(w,h)} :Brush "{ART}DA_HCA3_RoundBrush.DA_HCA3_RoundBrush")',box('Plate',f'(+ {x} {mul(5.0)})',f'(+ {y} {mul(7.0)})',f'(- {w} {mul(10.0)})',f'(- {h} {mul(12.0)})'),box('Inner',f'(+ {x} {mul(8.0)})',f'(+ {y} {mul(9.0)})',f'(- {w} {mul(16.0)})',mul(2.0))])
def text(expr,x,y,size=20,font=None,tint='(R=0.953,G=0.902,B=0.784,A=1)'):
 font=font or bodyfont
 tint_value=tint if tint.startswith('(select') else '"'+tint+'"'
 return '\n'.join([f'(Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) {expr}) :Position {xy(f"(+ {x} {mul(1.0)})",f"(+ {y} {mul(3.0)})")} :Font "{font}" :FontSize {mul(size)} :Tint "(R=0.118,G=0.141,B=0.2,A=1)")',f'(Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) {expr}) :Position {xy(x,y)} :Font "{font}" :FontSize {mul(size)} :Tint {tint_value})'])
SCALE='''(bind size (UserInterface|Geometry|GetLocalSize :Geometry (Widget|GetCachedGeometry)))
 (bind (width height) (Math|Vector2D|BreakVector2D :InVec size))
 (bind dpi (Math|Float|Max(Float) :A (UserInterface|Viewport|GetViewportScale) :B 0.01))
 (bind scale (/ (Math|Float|Clamp(Float) :Value (Math|Float|Min(Float) :A (/ (* width dpi) 1280.0) :B (/ (* height dpi) 720.0)) :Min 0.85 :Max 1.25) dpi))'''
GS='(Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))'
STATE='(bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))'
widget=ue.load_asset('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD')
# Repair the current invalid const graph before var()/fn() trigger any compilation.
write(widget,'OnPaint','','Context')
for name,kind,val in [('ObservedIndex','int',-1),('ObservedAttempt','int',-1),('SeenCleared','bool',False),('SeenFailed','bool',False),('MomentStarted','float',-10),('DisplayRoundName','string',''),('DisplayObjective','string',''),('DisplayTeam','string',''),('DisplayTools','string',''),('DisplaySpectator','string',''),('DisplayRelics','string',''),('DisplayedFlares','int',0),('DisplayedDead','bool',False),('ShowSixHUD','bool',False),('BigSixBanner','bool',False)]:var(widget,name,kind,val)
var(widget,'RosterLabels','string',array=True);var(widget,'RosterSlots','int',array=True)
for name in ('UpdateSixHUD','StartSixHUD','StopSixHUD'):fn(widget,name)
update=f'''
 (bind gs {GS} (:then {STATE}
  {S('ShowSixHUD','(not (Utilities|String|EqualExactly(String) :A (Class|BPCoopGameState|GetAreaName :self gs) :B "Egypt"))')}
  (bind now (GameState|GetServerWorldTimeSeconds :self gs))
  (bind cleared (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2")))
  (bind failed (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")))
  (if (or (!= index {V('ObservedIndex')}) (or (!= attempt {V('ObservedAttempt')}) (or (!= cleared {V('SeenCleared')}) (!= failed {V('SeenFailed')}))))
   {S('MomentStarted','now')} {S('ObservedIndex','index')} {S('ObservedAttempt','attempt')} {S('SeenCleared','cleared')} {S('SeenFailed','failed')})
  {S('BigSixBanner',f'(< (- now {V("MomentStarted")}) 3.0)')}
  {S('DisplayRoundName','(select (== index 0) "THE CAVE" (select (== index 1) "THE FIRST ROOM" (select (== index 2) "THE MAZE" (select (== index 3) "THE MEETING HALL" (select (== index 4) "THE DEEP MAZE" (select (== index 5) "THE RELIC" "THE ESCAPE"))))))')}
  {S('DisplayObjective','(select failed "Restarting at the checkpoint in 3 seconds." (select cleared "The way is open. Enter the maze together." (select (== index 0) "Stand together on the start pad." (select (== index 1) "Press every plate together." (select (== index 2) "Reach the meeting hall on your own path." (select (== index 3) "Light every lock at the same time." (select (== index 4) "Reach the relic chamber on your own path." (select (== index 5) "Hold the cage and lift the relic." "Carry the relic to the first-room altar."))))))))')}
  (if (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator4"))
   {S('DisplayObjective','"Relic delivered. Traveling to Map 2."')})
  (bind score (Utilities|String|BuildString(Integer) :Prefix "RELICS " :InInt (Class|BPCoopGameState|GetRelicsCollected :self gs) :Suffix " / "))
  {S('DisplayRelics','(Utilities|String|BuildString(Integer) :AppendTo score :InInt (Class|BPCoopGameState|GetRelicsAvailable :self gs))')}
  {S('DisplayTeam','""')}
  (Utilities|Array|Clear :TargetArray {V('RosterLabels')})
  (Utilities|Array|Clear :TargetArray {V('RosterSlots')})
  (for state (Class|GameStateBase|GetPlayerArray :self gs)
   (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object state)
    (:then (bind slot (Class|BPCoopPlayerState|GetColorSlot :self ps))
     (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object (PlayerState|GetPawn :self ps))
      (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
       (:then (bind dead (Class|ACHealth|IsDead :self health))
        (bind carrying (Class|BPCoopCharacter|GetCarryingRelic :self pawn))
        (bind label (Utilities|String|BuildString(Integer) :Prefix "P" :InInt (+ slot 1) :Suffix (select dead "  DEAD" (select carrying "  CARRYING" "  ALIVE"))))
        {S('DisplayTeam',f'(Utilities|String|Append {V("DisplayTeam")} (Utilities|String|Append label ";"))')}
        (Utilities|Array|Add :TargetArray {V('RosterLabels')} :NewItem label)
        (Utilities|Array|Add :TargetArray {V('RosterSlots')} :NewItem slot)) (:CastFailed))) (:CastFailed))) (:CastFailed)))
  (bind pc (Widget|GetOwningPlayer))
  (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object (Controller|GetControlledPawn :self pc))
   (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then {S('DisplayedDead','(Class|ACHealth|IsDead :self health)')}
     (bind tools (Utilities|Casting|CastToAC_Tools :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/Tools/AC_Tools.AC_Tools_C"))
      (:then {S('DisplayedFlares','(Class|ACTools|GetFlaresLeft :self tools)')}
       (bind view (Utilities|Casting|CastToAC_PlayerView :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/AC_PlayerView.AC_PlayerView_C"))
        (:then (bind lamp (Class|ACPlayerView|GetHeadlampOn :self view))
         {S('DisplayTools',f'(Utilities|String|BuildString(Integer) :Prefix (select lamp "LAMP ON   FLARES " "LAMP OFF  FLARES ") :InInt {V("DisplayedFlares")})')}
         {S('DisplaySpectator','""')}
         (if {V('DisplayedDead')}
          (bind watching (Class|ACPlayerView|GetLastSpectatorSlot :self view))
          {S('DisplaySpectator','(select (< watching 0) "DEAD - waiting for the checkpoint." (Utilities|String|BuildString(Integer) :Prefix "DEAD - watching P" :InInt (+ watching 1) :Suffix ". Interact switches view."))')})) (:CastFailed))) (:CastFailed))) (:CastFailed))) (:CastFailed))) (:CastFailed))'''
write(widget,'UpdateSixHUD',update)
write(widget,'StartSixHUD','(CallFunction|UpdateSixHUD) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "UpdateSixHUD" :Time 0.1 :bLooping true)')
write(widget,'StopSixHUD','(Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "UpdateSixHUD")')
event(widget,'Construct','StartSixHUD');event(widget,'Destruct','StopSixHUD')
# OnPaint is const: cached property getters and painting only, no setters or mutating calls.
body=SCALE+f'''
 (if {V('ShowSixHUD')}
  (bind big {V('BigSixBanner')})
  (bind bannerHeight (select big {mul(98.0)} {mul(62.0)}))
  (bind bannerWidth (Math|Float|Min(Float) :A {mul(640.0)} :B (- width {mul(48.0)})))
  {panel(mul(24.0),mul(24.0),'bannerWidth','bannerHeight')}
  {text(V('DisplayRoundName'),mul(38.0),mul(31.0),'(select big 28.0 20.0)',heading)}
  {text(V('DisplayObjective'),mul(38.0),'(select big (* 67.0 scale) (* 58.0 scale))',20,tint='(R=1,G=0.702,B=0.278,A=1)')}
  {panel(mul(24.0),'(- height (* 124.0 scale))',mul(300.0),mul(96.0))}
  {text(V('DisplayRelics'),mul(38.0),'(- height (* 118.0 scale))',22,heading,tint='(R=0.91,G=0.702,B=0.227,A=1)')}
  {text(V('DisplayTools'),mul(38.0),'(- height (* 85.0 scale))',20)}
  (bind rowCount (Utilities|Array|Length :TargetArray {V('RosterLabels')}))
  (bind teamY (- (- height (* 50.0 scale)) (* rowCount (* 30.0 scale))))
  {panel('(- width (* 250.0 scale))','teamY',mul(226.0),'(+ (* 30.0 scale) (* rowCount (* 30.0 scale)))')}
  (for row (range rowCount)
   (bind label (Utilities|Array|Get(acopy) {V('RosterLabels')} row))
   (bind slot (Utilities|Array|Get(acopy) {V('RosterSlots')} row))
   {text('label','(- width (* 238.0 scale))','(+ teamY (* (+ 10.0 (* 30.0 row)) scale))',20,tint='(select (== slot 0) (Math|Color|MakeLinearColor :R 0.32 :G 0.55 :B 0.9 :A 1.0) (select (== slot 1) (Math|Color|MakeLinearColor :R 0.9 :G 0.55 :B 0.65 :A 1.0) (select (== slot 2) (Math|Color|MakeLinearColor :R 0.55 :G 0.75 :B 0.68 :A 1.0) (Math|Color|MakeLinearColor :R 0.75 :G 0.58 :B 0.92 :A 1.0))))')})
  (if {V('DisplayedDead')}
   {panel(mul(24.0),mul(137.0),'bannerWidth',mul(80.0))}
   {text(V('DisplaySpectator'),mul(38.0),mul(145.0),20)}
   {text('"You return when the team regroups."',mul(38.0),mul(178.0),20)}))'''
write(widget,'OnPaint',body,'Context');save(widget)
prompt=ue.load_asset('/Game/Puzzles/UI/WBP_InteractPrompt')
update_before=BP.read_graph_dsl(BP.get_graph(prompt,'UpdatePrompt'))
# Existing prompt widget has an owned 330x170 area; stay within that rectangle.
pbody='''(if (Variables|Default|GetShowPrompt)
 (bind dpi (Math|Float|Max(Float) :A (UserInterface|Viewport|GetViewportScale) :B 0.01))
 (bind scale (/ 1.0 dpi))
'''+panel(mul(15.0),mul(26.0),mul(300.0),mul(106.0))+f'''
 (bind full (Utilities|String|ToString(Text) {V('Prompt')}))
 (bind short (select (> (Utilities|String|Len full) 25) (Utilities|String|Append (Utilities|String|Left :SourceString full :Count 22) "...") full))
 {text('short',mul(29.0),mul(38.0),20)}
 {text(f'(select {V("ShowProgress")} "Hold Interact" "Interact")',mul(29.0),mul(68.0),20)}
 (if {V('ShowProgress')}
  (Painting|DrawLine :Context Context :PositionA {xy(mul(29.0),mul(115.0))} :PositionB {xy(mul(301.0),mul(115.0))} :Thickness {mul(8.0)} :Tint "(R=0.118,G=0.141,B=0.2,A=1)")
  (Painting|DrawLine :Context Context :PositionA {xy(mul(29.0),mul(115.0))} :PositionB {xy(f'(* (+ 29.0 (* 272.0 {V("Progress")})) scale)',mul(115.0))} :Thickness {mul(6.0)} :Tint "(R=1,G=0.702,B=0.278,A=1)")))'''
write(prompt,'OnPaint',pbody,'Context');assert BP.read_graph_dsl(BP.get_graph(prompt,'UpdatePrompt'))==update_before;save(prompt)
results=ue.load_asset('/Game/Puzzles/UI/Results/WBP_RunResults')
rbody=SCALE+f'''
 (bind center (/ width 2.0))
 {panel('(- center (* 250.0 scale))','(* height 0.28)',mul(500.0),mul(212.0))}
 (Utilities|IsValid :InputObject {V('Coordinator')} (:"Is Valid"
  (bind co {V('Coordinator')})
  (bind collected (Utilities|String|BuildString(Integer) :Prefix "RELICS " :InInt (Class|BPRunCoordinator|GetCapturedCollected :self co) :Suffix " / "))
  (bind total (Utilities|String|BuildString(Integer) :AppendTo collected :InInt (Class|BPRunCoordinator|GetCapturedAvailable :self co)))
  {text('"MISSION COMPLETE"','(- center (* 220.0 scale))','(+ (* height 0.28) (* 18.0 scale))',30,heading)}
  {text('total','(- center (* 220.0 scale))','(+ (* height 0.28) (* 73.0 scale))',26,heading,tint='(R=0.91,G=0.702,B=0.227,A=1)')}
  (bind pc (Widget|GetOwningPlayer))
  (bind host (and (Networking|HasAuthority :self pc) (Game|Player|IsPrimaryPlayer :self pc)))
  (bind instruction (select (Class|BPRunCoordinator|GetRestartInProgress :self co) "RESTARTING..." (select host "R / START: BEGIN A NEW RUN" "WAITING FOR THE HOST")))
  {text('instruction','(- center (* 220.0 scale))','(+ (* height 0.28) (* 143.0 scale))',20)}
 ) (:"Is Not Valid"))'''
write(results,'OnPaint',rbody,'Context');save(results)
RESULT={'writes':[widget.get_path_name(),prompt.get_path_name(),results.get_path_name()]+[UI+'DA_'+n+'Brush' for n in colors], 'presentation_only':True,'font_heading':heading,'font_body':bodyfont,'font_acceptance_pending':heading.startswith('/Engine/') or bodyfont.startswith('/Engine/'),'runtime_visual_acceptance_pending':True}
