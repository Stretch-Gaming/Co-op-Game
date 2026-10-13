"""HC authoring context, exact package saves and reservations."""
import sys,json
from pathlib import Path
import unreal as ue
ROOT=Path(ue.Paths.project_dir()).resolve();assert ROOT==Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent;QUEUE=ROOT/'Saved/MazeLevel'
sys.path.insert(0,str(ROOT/'Tools/unreal/six_round'))
import authoring
authoring.ROOT=ROOT;authoring.EXPECTED=ROOT;authoring.QUEUE=QUEUE
from authoring import BP,AT,V,S,fn,var,create,write,component,compile_bp,save,event
MODE='/Game/Puzzles/Test/SixRound/BP_SixRoundTestGameMode'
HC='/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test'
WORLD='/Game/Hazards/Test/SixRound/L_WorldRoute_Test'
CAVE='/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test'
PG='/Game/Player/Test/SixRound/L_SixRound_PG_Test'
ENTRY='/Game/Puzzles/Test/SixRound/L_SixRound_Test'
_base_write=write
def write(bp,name,body,parameters=''):
    original=BP.create_node
    def make_node(graph,type_id,pos,declaring_class=None):
        inherited={'RefreshSixObjective','ClearRound','FailRound','CacheRelicHome','RestoreMissingRelic'}
        if bp.get_path_name().split('.')[0]==MODE and type_id.startswith('CallFunction|') and type_id.rsplit('|',1)[-1] in inherited:
            declaring_class=ue.load_asset('/Game/Core/BP_CoopGameMode').generated_class()
        if bp.get_path_name().split('.')[0]=='/Game/Puzzles/Test/SixRound/BP_TeamHallDoor' and type_id=='CallFunction|ApplyDoor':
            declaring_class=ue.load_asset('/Game/Puzzles/BP_MazeDoor').generated_class()
        return original(graph,type_id,pos,declaring_class=declaring_class)
    BP.create_node=staticmethod(make_node)
    try:return _base_write(bp,name,body,parameters)
    finally:BP.create_node=original
def override(bp,name):
    graph=next((g for g in BP.list_graphs(bp) if g.get_name()==name),None)
    if not graph:graph=ue.BlueprintEditorLibrary.add_function_override(bp,ue.Name(name))
    assert graph,('Native function override required',name)
    return graph
def lease(path):
    relative='Content/'+path.removeprefix('/Game/')+('.umap' if path.startswith('/Game/') and path.rsplit('/',1)[-1].startswith('L_') else '.uasset')
    rows=json.loads((QUEUE/'leases.json').read_text(encoding='utf-8-sig'))
    assert len([r for r in rows if r['path']==relative and r.get('owner',{}).get('name')=='StretchGaming'])==1,relative
def save_level(level):
    package=level.get_outermost();path=package.get_name()
    assert path in (HC,WORLD,CAVE,PG)
    if path in (WORLD,PG):lease(path)
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    assert ue.EditorLoadingAndSavingUtils.save_packages([package],False)
