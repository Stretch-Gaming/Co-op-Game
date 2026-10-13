import hashlib,json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');D=Path('/tmp/coop-runtime');args=json.loads((D/'fixed-hud-args.json').read_text());OUT=D/(args.get('report_name','fixed-hud-'+args['profile']+'-'+str(args['players']))+'.json');R={'passed':False,'rendered_pixel_acceptance':False,'packages_saved':[],'profile':args['profile'],'players':args['players'],'fixture':'CreatePlayer only for host secondary when profile=host_split; snapshot injects no input/gameplay changes'}
try:
 assert Path(ue.Paths.project_dir()).resolve()==ROOT
 build=json.loads(Path('/tmp/coop-audit/runtime-evidence/internal-widget-geometry-v3-build.json').read_text());assert build['passed']
 probe=ue.load_object(None,build['cdo']);assert probe and probe.get_class().get_path_name()==build['generated_class']
 worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=[w for w in worlds if ue.GameplayStatics.get_game_mode(w)];assert len(server)==1
 C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();H=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
 server_pawns=list(ue.GameplayStatics.get_all_actors_of_class(server[0],C));ids={p.player_state.player_id for p in server_pawns};assert len(ids)==args['players']
 rows=[]
 for world in worlds:
  for p in ue.GameplayStatics.get_all_actors_of_class(world,C):
   if not p.is_locally_controlled():continue
   pc=p.get_controller();assert pc and pc.is_local_controller();cs=p.get_components_by_class(H);assert len(cs)==1
   hud=cs[0].get_editor_property('HUDWidget');prompt=p.get_editor_property('PromptWidget');assert hud and prompt
   assert all(w.get_owning_player()==pc and w.is_in_viewport() for w in (hud,prompt))
   active=[w for w in ue.ObjectIterator(ue.UserWidget) if w.get_owning_player()==pc and w.is_in_viewport()]
   assert sum(w.get_class()==hud.get_class() for w in active)==1 and sum(w.get_class()==prompt.get_class() for w in active)==1
   assert hud.get_editor_property('ShowSixHUD') and not hud.get_editor_property('DisplayedDead')
   assert pc.get_view_target()==p
   size=probe.call_method(build['function'],args=(hud,));assert size.x>1 and size.y>1
   rows.append({'owner_id':p.player_state.player_id,'world':world.get_path_name(),'pawn':p.get_path_name(),'controller':pc.get_path_name(),'primary':pc.is_primary_player(),'hud':hud.get_path_name(),'prompt':prompt.get_path_name(),'hud_local_size':[size.x,size.y],'ShowSixHUD':hud.get_editor_property('ShowSixHUD'),'DisplayRoundName':hud.get_editor_property('DisplayRoundName'),'DisplayObjective':hud.get_editor_property('DisplayObjective'),'DisplayTools':hud.get_editor_property('DisplayTools'),'DisplayTeam':hud.get_editor_property('DisplayTeam'),'DisplayedDead':hud.get_editor_property('DisplayedDead'),'DisplayedFlares':hud.get_editor_property('DisplayedFlares')})
 assert len(rows)==len(ids) and {r['owner_id'] for r in rows}==ids
 assert len({r['hud'] for r in rows})==len(rows) and len({r['prompt'] for r in rows})==len(rows)
 if args['profile']=='host_split':
  hosts=[r for r in rows if r['world']==server[0].get_path_name()];assert len(hosts)==2 and {r['primary'] for r in hosts}=={True,False}
 R.update({'passed':True,'owners':rows,'worlds':[w.get_path_name() for w in worlds],'native_log_scan_pending':True,'current_widget_sha256':{p:hashlib.sha256((ROOT/'Content'/(p[6:]+'.uasset')).read_bytes()).hexdigest() for p in json.loads((D/'hud-paint-float-repair.json').read_text())['packages_saved']}})
except Exception:R['error']=traceback.format_exc()
OUT.write_text(json.dumps(R,indent=2))
