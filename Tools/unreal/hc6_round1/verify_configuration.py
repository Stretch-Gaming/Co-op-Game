"""Focused readback and fail-closed test, after the movement matrix finishes."""
import sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
worlds=list(unreal.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if unreal.GameplayStatics.get_game_state(w).has_authority())
cls=unreal.load_class(None,'/Game/Puzzles/BP_PuzzleSetup.BP_PuzzleSetup_C')
setups={w:unreal.GameplayStatics.get_all_actors_of_class(w,cls)[0] for w in worlds}
current=setups[server]
statue_class=current.get_editor_property('StatueClass')
expected=current.get_editor_property('StatueCount')
report={'project':str(ROOT),'fixture_only':True,'replicated_spawns':[]}
for w in worlds:
    items=unreal.GameplayStatics.get_all_actors_of_class(w,statue_class)
    assert len(items)==expected,(w.get_path_name(),len(items),expected)
    report['replicated_spawns'].append({'world':w.get_path_name(),'count':len(items),'locations':[[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z] for a in items]})
gm=unreal.GameplayStatics.get_game_mode(server)
current.set_editor_property('StatueClass',None)
gm.call_method('StartRound',args=(1,))
configuration_state={'phase':0,'began':time.monotonic()}
def config_tick(dt):
    try:
        if time.monotonic()-configuration_state['began']<1:return
        if configuration_state['phase']==0:
            assert all(not s.get_editor_property('Ready') for s in setups.values())
            assert all(len(unreal.GameplayStatics.get_all_actors_of_class(w,statue_class))==0 for w in worlds)
            report['null_class_fails_closed']=True
            current.set_editor_property('StatueClass',statue_class)
            gm.call_method('StartRound',args=(1,))
            configuration_state['phase']=1;configuration_state['began']=time.monotonic();return
        assert all(s.get_editor_property('Ready') for s in setups.values())
        assert all(len(unreal.GameplayStatics.get_all_actors_of_class(w,statue_class))==expected for w in worlds)
        report['restored_class_respawns']=True;report['passed']=True
        (OUT/'configuration-verification.json').write_text(json.dumps(report,indent=2))
        unreal.unregister_slate_post_tick_callback(configuration_state['handle'])
    except Exception:
        report['passed']=False;report['error']=traceback.format_exc()
        (OUT/'configuration-verification.json').write_text(json.dumps(report,indent=2))
        unreal.unregister_slate_post_tick_callback(configuration_state['handle'])
configuration_state['handle']=unreal.register_slate_post_tick_callback(config_tick)
