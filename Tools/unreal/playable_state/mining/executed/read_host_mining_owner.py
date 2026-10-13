import json
from pathlib import Path
import unreal as ue
assert Path(ue.Paths.project_dir()).resolve()==Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
assert len(worlds)==3 and not ue.SystemLibrary.is_dedicated_server(server)
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();rows=[]
for p in ue.GameplayStatics.get_all_actors_of_class(server,C):
 pc=p.get_controller();rows.append({'id':p.player_state.player_id,'slot':p.player_state.get_editor_property('ColorSlot'),'local':p.is_locally_controlled(),'controller':pc.get_path_name(),'primary':pc.is_primary_player()})
host=[r for r in rows if r['local']];assert len(host)==2
chosen=next(r for r in host if r['slot']==3);assert not chosen['primary']
Path('/tmp/coop-runtime/host-mining-owner.json').write_text(json.dumps({'passed':True,'players':4,'profile':'host_split','mining_owner_ordinal':3,'secondary_host_owner':chosen,'roster':rows,'read_only':True},indent=2))
