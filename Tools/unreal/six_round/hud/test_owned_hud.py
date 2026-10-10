"""Runtime UI ownership/data/bounds gate, read-only. Run fresh 2/3/4-player PIE
and again in both local split layouts and on the results map. No UI state setters.
"""
import json,re,traceback
from pathlib import Path
import unreal as ue
ROOT=Path(ue.Paths.project_dir()).resolve();assert ROOT==Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')
QUEUE=ROOT/'Saved/SixRound';QUEUE.mkdir(parents=True,exist_ok=True)
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();HUD=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class();H=ue.load_asset('/Game/Hazards/AC_Health').generated_class();U=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class();RES=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults').generated_class()
expected_names={0:'THE CAVE',1:'THE FIRST ROOM',2:'THE MAZE',3:'THE MEETING HALL',4:'THE DEEP MAZE',5:'THE RELIC',6:'THE ESCAPE'}
report={'passed':False,'checks':[],'visual_check_pending':True}
try:
 owners=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()];assert len(owners) in (2,3,4)
 widgets=[]
 for pawn in owners:
  pc=pawn.get_controller();world=pawn.get_world();gs=ue.GameplayStatics.get_game_state(world);area=gs.get_editor_property('AreaName')
  hud=pawn.get_component_by_class(HUD);assert hud
  widget=hud.get_editor_property('HUDWidget');assert widget and widget.get_owning_player()==pc
  assert hud.get_editor_property('HUDController')==pc;widgets.append(widget.get_path_name())
  screen=ue.WidgetLayoutLibrary.get_player_screen_widget_geometry(pc);screen_size=ue.SlateBlueprintLibrary.get_local_size(screen);hud_size=ue.SlateBlueprintLibrary.get_local_size(widget.get_cached_geometry())
  assert screen_size.x>100 and screen_size.y>100
  assert abs(hud_size.x-screen_size.x)<max(4,screen_size.x*.03) and abs(hud_size.y-screen_size.y)<max(4,screen_size.y*.03),(hud_size,screen_size)
  if area!='Egypt':
   state=gs.get_editor_property('RoundState');idx=state.get_editor_property('Index_11_91104438409472A6DD374BADC8DC29B1')
   assert widget.get_editor_property('DisplayRoundName')==expected_names[idx]
   assert widget.get_editor_property('DisplayedFlares')==pawn.get_component_by_class(U).get_editor_property('FlaresLeft')
   assert widget.get_editor_property('DisplayedDead')==pawn.get_component_by_class(H).get_editor_property('bDead')
   displayed=widget.get_editor_property('DisplayTeam')
   for ps in gs.player_array:
    teammate=ps.get_pawn();assert teammate,'Wait until the full replicated roster has possessed pawns'
    slot=ps.get_editor_property('ColorSlot');dead=teammate.get_component_by_class(H).get_editor_property('bDead')
    carry=teammate.get_component_by_class(ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()).get_editor_property('CarriedItem')
    carrying=carry is not None and carry.actor_has_tag('Relic')
    label=f'P{slot+1}  '+('DEAD' if dead else ('CARRYING' if carrying else 'ALIVE'));assert label+';' in displayed,(label,displayed)
   prompt=pawn.get_editor_property('PromptWidget');assert prompt and prompt.get_owning_player()==pc
   if widget.get_editor_property('DisplayedDead'):
    spectator=widget.get_editor_property('DisplaySpectator');view=pawn.get_component_by_class(ue.load_asset('/Game/Player/AC_PlayerView').generated_class());slot=view.get_editor_property('LastSpectatorSlot')
    assert ('waiting for the checkpoint' in spectator) if slot<0 else (f'watching P{slot+1}' in spectator)
   roster_slots=list(widget.get_editor_property('RosterSlots'));roster_labels=list(widget.get_editor_property('RosterLabels'))
   assert len(roster_labels)==len(gs.player_array) and len(roster_slots)==len(roster_labels)
   assert set(roster_slots)==set(ps.get_editor_property('ColorSlot') for ps in gs.player_array)
  else:
   results=pc.get_component_by_class(RES);rw=results.get_editor_property('ResultsWidget');assert rw and rw.get_owning_player()==pc
   size=ue.SlateBlueprintLibrary.get_local_size(rw.get_cached_geometry());assert abs(size.x-screen_size.x)<max(4,screen_size.x*.03) and abs(size.y-screen_size.y)<max(4,screen_size.y*.03)
  report['checks'].append({'player_id':pawn.player_state.player_id,'world':world.get_name(),'area':area,'hud_owned':True,'local_size':[hud_size.x,hud_size.y],'screen_size':[screen_size.x,screen_size.y],'live_game_state_and_component_values_match':True})
 assert len(set(widgets))==len(owners),'Each local view needs its own HUD instance'
 report['passed']=True
except Exception:report['error']=traceback.format_exc()
(QUEUE/'hud-owned-readback.json').write_text(json.dumps(report,indent=2));RESULT=report
