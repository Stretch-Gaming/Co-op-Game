"""L_Site01 baseline client smoke; HC6 placement is explicitly absent."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
worlds=list(unreal.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if unreal.GameplayStatics.get_game_state(w).has_authority())
assert len([p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.Pawn) if p.get_editor_property('player_state')])==2
report={'project':str(ROOT),'map':'/Game/Maps/L_Site01','mode':'Play As Client','players':2,
 'integrated_round1_verified':False,'reason':'Cave placement is exclusively owned by the cave chat; no HC6 actor placements were saved here.','worlds':[]}
for w in worlds:
    gs=unreal.GameplayStatics.get_game_state(w)
    assert gs
    pcs=[pc for pc in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.PlayerController) if pc.is_local_controller()]
    for pc in pcs:assert pc.get_controlled_pawn()
    counts={name:len(unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_class(None,'/Game/Puzzles/'+name+'.'+name+'_C'))) for name in ACTORS}
    assert not any(counts.values())
    report['worlds'].append({'world':w.get_path_name(),'authority':gs.has_authority(),'local_controllers':len(pcs),'hc6_actor_counts':counts})
assert sum(x['local_controllers'] for x in report['worlds'])==2
report['baseline_smoke_passed']=True
(OUT/'integrated-smoke.json').write_text(json.dumps(report,indent=2))
