import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
world=next(w for w in ue.EditorLevelLibrary.get_pie_worlds(True) if ue.GameplayStatics.get_game_mode(w))
RESULT={'actors':[],'graphs':{}}
for path,names in [('/Game/Player/RelicChamber/BP_Lever',('CanInteract','GetInteractInfo','BeginHold','LeverBeginAdapter','CheckHolder','UpdateHandle','EventGraph')),('/Game/Player/RelicChamber/BP_RelicCage',('CageAuthorityTick','BeginCage'))]:
    bp=ue.load_asset(path)
    RESULT['graphs'][path]={n:BP.read_graph_dsl(BP.get_graph(bp,n)) for n in names}
    variables=list(BP.list_variables(bp))
    for actor in ue.GameplayStatics.get_all_actors_of_class(world,bp.generated_class()):
        row={'label':actor.get_actor_label(),'class':actor.get_class().get_path_name(),'variables':{},'position':str(actor.get_actor_location())}
        for name in variables:
            if any(s.lower() in name.lower() for s in ('held','holder','raised','latched','lever')):
                try:row['variables'][name]=str(actor.get_editor_property(name))
                except Exception as e:row['variables'][name]=str(e)
        RESULT['actors'].append(row)
(QUEUE/'cage-runtime-diagnostic.json').write_text(__import__('json').dumps(RESULT,indent=2))
