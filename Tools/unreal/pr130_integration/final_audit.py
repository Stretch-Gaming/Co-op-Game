"""Read saved composition, collision import, protected bytes and touched-graph policy."""
import hashlib,json,sys
sys.path.insert(0,str(HERE))
from context import *
bp=ue.load_asset('/Game/Player/Tools/BP_Flare')
flags=[]
for graph in BP.list_graphs(bp):
    for node in BP.find_nodes(graph):
        kind=str(BP._get_node_info(node).type_id).lower()
        if any(x in kind for x in ('getplayercharacter','getplayercontroller','getplayerpawn','addtoviewport')):flags.append(kind)
assert not flags,flags
mesh=ue.load_asset('/Game/Player/Art/Flares/SM_HandFlare')
subsystem=ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
collision=subsystem.get_convex_collision_count(mesh)
assert collision==1,collision
baseline=json.loads((QUEUE/'baseline.json').read_text())['hashes']
protected={p:h for p,h in baseline.items() if p not in ('Content/Hazards/Test/SixRound/L_WorldRoute_Test.umap','Content/Player/Tools/BP_Flare.uasset')}
after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected}
assert after==protected, 'Protected original file changed'
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ue.GameplayStatics.flush_level_streaming(world)
levels=sorted(l.get_outermost().get_name() for l in ue.EditorLevelUtils.get_levels(world))
expected=sorted(json.loads((QUEUE/'baseline.json').read_text())['levels'])
assert levels==expected
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()
doors=[a for a in actors if a.actor_has_tag('ConnectionDoor')]
assert len(doors)==1
maze=[a for a in actors if a.actor_has_tag('PR130.TeamMaze')]
assert len(maze)==516
report={'passed':True,'levels':levels,'puzzle_doors':1,'team_maze_actors':516,'imported_flare_convex_hulls':collision,
        'protected_sha256':after,'touched_blueprint_graph_policy_flags':flags,'no_runtime_cpp_or_config_changes':True}
(QUEUE/'final-audit.json').write_text(json.dumps(report,indent=2));RESULT=report
