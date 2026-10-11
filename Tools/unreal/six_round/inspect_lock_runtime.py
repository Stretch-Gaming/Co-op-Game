"""Read only actual light-source and tool state during a stalled lock gate."""
import unreal as ue
world=next(w for w in ue.EditorLevelLibrary.get_pie_worlds(True) if ue.GameplayStatics.get_game_mode(w))
items=[]
for name in ('BP_CrystalLock','BP_Flare'):
    path='/Game/Puzzles/'+name if name=='BP_CrystalLock' else '/Game/Player/Tools/'+name
    for actor in ue.GameplayStatics.get_all_actors_of_class(world,ue.load_asset(path).generated_class()):
        row={'class':name,'label':actor.get_actor_label(),'position':str(actor.get_actor_location())}
        for key in (('Enabled','Lit','Brazier','SourceCount','LightSources') if name=='BP_CrystalLock' else ('BurnStarted','BurnSeconds','LightTarget')):
            value=actor.get_editor_property(key)
            row[key]=str(value)
        items.append(row)
RESULT=items
