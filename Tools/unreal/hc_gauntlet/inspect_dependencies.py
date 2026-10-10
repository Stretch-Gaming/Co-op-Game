"""Read the delivered ghost lifecycle/target graphs and exact dependency presence."""
import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
paths=['/Game/Player/Ghosts/BP_Ghost','/Game/Player/Ghosts/BP_GhostSpawner','/Game/Player/AC_PlayerView','/Game/Player/BPFL_SplitScreen','/Game/Player/Round3/BP_ExitLever','/Game/Hazards/AC_Health','/Game/Hazards/BP_SpikeTrap','/Game/Hazards/BP_DartTrap','/Game/Hazards/BP_SwingingTrap']
report={'present':{p:ue.EditorAssetLibrary.does_asset_exist(p) for p in paths},'hazard_assets':list(ue.EditorAssetLibrary.list_assets('/Game/Hazards',True,False)),'ghost':{}}
bp=ue.load_asset('/Game/Player/Ghosts/BP_Ghost')
if bp:
 graphs=BP.list_graphs(bp)
 d=ue.get_default_object(bp.generated_class())
 report['ghost']={'variables':list(BP.list_variables(bp)),'round_reset_interface':ue.SystemLibrary.does_implement_interface(d,ue.load_asset('/Game/Core/BPI_RoundReset').generated_class()),'replicates':bool(d.get_editor_property('replicates')),'replicate_movement':bool(d.get_editor_property('replicate_movement')),'graph_names':[g.get_name() for g in graphs],'selected_graphs':{g.get_name():BP.read_graph_dsl(g) for g in graphs if g.get_name()!='UserConstructionScript'}}
(HERE/'dependency-inspection.json').write_text(json.dumps(report,indent=2))
