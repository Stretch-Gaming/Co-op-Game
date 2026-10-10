import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
editor=unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
for name in ACTORS:editor.close_all_editors_for_asset(unreal.load_asset('/Game/Puzzles/'+name))
worlds=unreal.EditorLevelLibrary.get_pie_worlds(True)
host=next(w for w in worlds if unreal.GameplayStatics.get_game_state(w).has_authority())
pcs=[pc for pc in unreal.ObjectIterator(unreal.PlayerController) if pc.get_world()==host and pc.is_local_controller() and pc.get_controlled_pawn()]
assert len(pcs)==2
pcs.sort(key=lambda pc:pc.get_editor_property('player_state').get_editor_property('player_id'))
for i,pc in enumerate(pcs):
    pc.get_controlled_pawn().set_actor_location(unreal.Vector(-550,-100+200*i,92.15),False,True)
    pc.set_control_rotation(unreal.Rotator(pitch=-10,yaw=0,roll=0))
(OUT/'host-view.json').write_text(json.dumps({'host':host.get_path_name(),'local_players':len(pcs),'controllers':[pc.get_path_name() for pc in pcs]},indent=2))
