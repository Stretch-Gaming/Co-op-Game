"""Independent final Blueprint/package audit. Run with PIE stopped."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
assert not unreal.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE before compiling'
interface=unreal.load_asset('/Game/Core/BPI_RoundReset').generated_class()
report={'project':str(ROOT),'engine':unreal.SystemLibrary.get_engine_version(),'actors':{},'saved_packages':[]}
rep={'BP_PressurePlate':['Pressed','Enabled'],'BP_PuzzleSetup':['Ready','PlateCount','StatueCount'],'BP_ChamberGate':['Open'],'BP_StartPad':['Started']}
for name in ACTORS:
    bp=unreal.load_asset('/Game/Puzzles/'+name)
    compile_bp(bp)
    cdo=BP.get_default_object(bp)
    assert cdo.get_editor_property('replicates')
    assert unreal.SystemLibrary.does_implement_interface(cdo,interface)
    graphs={}
    for g in BP.list_graphs(bp):
        infos=BP.get_node_infos(BP.find_nodes(g))
        ids=[str(n.type_id) for n in infos]
        assert not any('GetPlayerCharacter' in s or 'GetPlayerPawn' in s or 'GetPlayerController' in s for s in ids),(name,g.get_name())
        assert not any('SetRoundPhase' in s or 'SetRoundState' in s for s in ids),(name,g.get_name())
        graphs[g.get_name()]={'node_count':len(ids),'type_ids':ids,
          'own_calls':[{'id':n.type_id,'self_type':next((p.type_id for p in n.input_pins if p.name=='self'),None)} for n in infos if str(n.type_id).startswith('|') and not isinstance(n.node,(unreal.K2Node_FunctionEntry,unreal.K2Node_FunctionResult))]}
    replication={n:str(BP.get_variable_replication(bp,n)) for n in rep[name]}
    assert all('REP_NOTIFY' in value for value in replication.values())
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
    report['actors'][name]={'compile':str(bp.get_editor_property('status')),'round_reset':True,'replicates':True,
      'always_relevant':cdo.get_editor_property('always_relevant'),'replication':replication,'graphs':graphs}
    report['saved_packages'].append(bp.get_outermost().get_name())
for name in ('BP_HC6FixtureGameMode','BP_HC6TestWeight'):
    bp=unreal.load_asset('/Game/Puzzles/Test/HC6/'+name);compile_bp(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    report['saved_packages'].append(bp.get_outermost().get_name())
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()=='/Game/Puzzles/Test/HC6/L_HC6_Round1'
assert unreal.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],True)
report['saved_packages'].append(world.get_outermost().get_name())
report['dirty_unowned_packages']=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
 if p.get_name() not in report['saved_packages'] and not p.get_name().startswith('/Game/Puzzles/Test/HC6/')]
report['passed']=not report['dirty_unowned_packages']
(OUT/'audit.json').write_text(json.dumps(report,indent=2))
assert report['passed'],report['dirty_unowned_packages']
