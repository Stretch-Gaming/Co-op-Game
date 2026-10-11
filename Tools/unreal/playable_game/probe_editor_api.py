import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.object import ObjectTools
from editor_toolset.toolsets.data_table import DataTableTools

health = ue.load_asset('/Game/Hazards/AC_Health')
graph = BP.get_graph(health,'ApplyHealthState')
needles = ['OnDowned','OnRevived','GetTags','DisableMovement','SetMovementMode','GetServerWorldTimeSeconds','SetUseControllerRotationYaw','IsPrimaryPlayer','InjectInputVector']
matches = {n: BP.find_node_types(graph,n) for n in needles}
report = {'struct_apis':[n for n in dir(ue) if any(s in n for s in ('StructEditor','StructUtils','StructureFactory','UserDefinedStructEditor'))], 'health_graphs':[g.get_name() for g in BP.list_graphs(health)], 'node_types':matches}
factory = ue.StructureFactory()
assets = ue.AssetToolsHelpers.get_asset_tools()
struct = ue.load_asset('/Game/Hazards/S_HazardScaling') or assets.create_asset('S_HazardScaling','/Game/Hazards',ue.UserDefinedStruct,factory)
assert struct
report['struct_class'] = struct.get_class().get_path_name()
report['struct_editor_property_schema'] = ObjectTools.list_properties(struct)
report['struct_methods'] = [n for n in dir(struct) if 'variable' in n.lower() or 'editor' in n.lower()]
try:
    editor_data = struct.get_editor_property('editor_data')
    report['struct_editor_data_class'] = editor_data.get_class().get_path_name()
    report['struct_editor_data_schema'] = ObjectTools.list_properties(editor_data)
except Exception as error:
    report['struct_editor_data_error'] = str(error)
(QUEUE/'editor-api-probe.json').write_text(json.dumps(report,default=str,indent=2))
RESULT = {'struct':struct.get_path_name(),'struct_apis':report['struct_apis'],'health_graphs':report['health_graphs'],'node_types':matches,'report':'Saved/PlayableGame/editor-api-probe.json'}
