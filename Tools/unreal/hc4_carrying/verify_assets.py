"""Read-only verification of saved class contracts and Core handoff signatures."""
import sys,pathlib,importlib,json,dataclasses
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
result={}
paths=['/Game/Puzzles/'+n for n in ['BP_Carryable','BP_KeyRelic','BP_Statue']]
paths+=['/Game/Puzzles/Carrying/AC_Carrying']
paths+=['/Game/Puzzles/Test/HC4/'+n for n in ['BP_HC4Character','BP_HC4Controller','BP_HC4GameMode']]
for path in paths:
    bp=unreal.load_asset(path)
    assert bp and bp.get_editor_property('status')==unreal.BlueprintStatus.BS_UP_TO_DATE,path
    cdo=BP.get_default_object(bp)
    row={'status':str(bp.get_editor_property('status')),'parent':unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp).get_path_name()}
    if isinstance(cdo,unreal.StaticMeshActor):
        mesh=cdo.static_mesh_component
        row.update({'replicates':cdo.get_editor_property('replicates'),'movement':cdo.get_editor_property('replicate_movement'),'root_mesh':cdo.root_component==mesh,
          'mobility':str(mesh.mobility),'overlaps':mesh.get_editor_property('generate_overlap_events'),'heavy':cdo.get_editor_property('Heavy')})
        assert row['replicates'] and row['movement'] and row['root_mesh']
        assert row['overlaps']
        assert mesh.mobility==unreal.ComponentMobility.MOVABLE
    if path.endswith('AC_Carrying'):
        row['replicated']=cdo.get_editor_property('replicates')
        assert row['replicated']
    if path.endswith('BP_Carryable'):
        row['events']=[str(e.name) for e in BP.list_events(bp)]
        assert 'ResetForRound' in row['events'] and 'Interact' in row['events']
        row['replication']={name:str(BP.get_variable_replication(bp,name)) for name in ['CarryState','Carrier']}
    if path.endswith('BP_HC4Character'):
        parts=[unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)) for h in AT._get_subobject_handles(AT._sds(),cdo,bp)]
        ac=unreal.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
        row['components']=[p.get_name() for p in parts if p and p.get_class()==ac]
        assert row['components']==['Carrying_GEN_VARIABLE']
        row['input_links']={}
        for n in BP.find_nodes(BP.get_graph(bp,'EventGraph')):
            info=BP.get_node_infos([n])[0]
            if 'EnhancedInputAction' in info.type_id:
                started=n.find_output_pin('Started')
                row['input_links'][info.type_id]=len(started.list_connected_pins())
                assert len(started.list_connected_pins())==1
    result[path]=row
core=unreal.load_asset('/Game/Core/BP_CoopCharacter')
result['Core_handoff']={}
for name in ['GetCarried','ReleaseCarried']:
    graph=BP.get_graph(core,name)
    result['Core_handoff'][name]=[{'type':info.type_id,'inputs':[{'name':p.name,'type':p.type_id} for p in info.input_pins],'outputs':[{'name':p.name,'type':p.type_id} for p in info.output_pins]} for info in BP.get_node_infos(BP.find_nodes(graph))]
out=ROOT/'Tools/unreal/hc4_carrying/evidence/saved_assets.json'
out.write_text(json.dumps(result,default=str,indent=2),encoding='utf-8')
RESULT={p:r for p,r in result.items() if p!='Core_handoff'}
