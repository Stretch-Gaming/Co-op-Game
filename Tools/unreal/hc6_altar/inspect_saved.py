import pathlib,json,unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT
bp=unreal.load_asset('/Game/Puzzles/BP_Altar');assert not unreal.EditorLevelLibrary.get_pie_worlds(True);assert bp.status==unreal.BlueprintStatus.BS_UP_TO_DATE
out={'status':str(bp.status),'variables':list(BP.list_variables(bp)),'functions':[g.get_name() for g in BP.list_graphs(bp)]}
for name in ['Completed','PlacedKey']:out[name]=str(BP.get_variable_replication(bp,name))
cdo=BP.get_default_object(bp);out['replicates']=cdo.replicates;out['always_relevant']=cdo.always_relevant
sds=AT._sds();parts=[unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)) for h in AT._get_subobject_handles(sds,cdo,bp)]
socket=next(p for p in parts if p and p.get_name().removesuffix('_GEN_VARIABLE')=='AltarSocket');out['socket_template']=str(socket.get_editor_property('relative_location'))
assert abs(socket.relative_location.z-125.305)<.001
assert not any(n in out['variables'] for n in ['CarryState','Carrier','Heavy','CarrierComponent'])
out['interfaces']={n:unreal.SystemLibrary.does_implement_interface(cdo,unreal.load_asset('/Game/Core/'+n).generated_class()) for n in ['BPI_Interactable','BPI_RoundReset']}
assert all(out['interfaces'].values())
pathlib.Path(__file__).parent.joinpath('saved-contracts.json').write_text(json.dumps(out,indent=2));RESULT=out
