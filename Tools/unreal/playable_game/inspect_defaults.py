import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
report={}
for path in ARGS['assets']:
    bp=ue.load_asset(path);cdo=BP.get_default_object(bp)
    report[path]={'defaults':{str(v):str(cdo.get_editor_property(str(v))) for v in BP.list_variables(bp)},'graphs':{g.get_name():len(BP.find_nodes(g)) for g in BP.list_graphs(bp)}}
    sds=ue.get_engine_subsystem(ue.SubobjectDataSubsystem);lib=ue.SubobjectDataBlueprintFunctionLibrary
    report[path]['components']=[{'name':str(lib.get_variable_name(lib.get_data(h))),'class':lib.get_object_for_blueprint(lib.get_data(h),bp).get_class().get_name()} for h in sds.k2_gather_subobject_data_for_blueprint(bp) if lib.get_object_for_blueprint(lib.get_data(h),bp)]
(QUEUE/'asset-details.json').write_text(json.dumps(report,indent=2))
RESULT=report

