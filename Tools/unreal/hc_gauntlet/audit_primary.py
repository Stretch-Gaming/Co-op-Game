"""Independent primary audit. Reads/compiles only owned packages; saves none."""
import json, hashlib, re
from pathlib import Path
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert Path(ue.Paths.project_dir()).resolve()==ROOT
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-58210709')
assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Compile with PIE stopped'
report={'project':str(ROOT),'session':SESSION,'engine':ue.SystemLibrary.get_engine_version(),'passed':False,'assets':[]}
interfaces={name:ue.load_asset('/Game/Core/'+name).generated_class() for name in ['BPI_Interactable','BPI_RoundReset']}
for folder in ['/Game/Puzzles/Gauntlet','/Game/Puzzles/Test/HC_Gauntlet']:
 for path in ue.EditorAssetLibrary.list_assets(folder, True, False):
  bp=ue.load_asset(path)
  if not isinstance(bp,ue.Blueprint): continue
  with toolset_registry.tool_raising_exceptions():
   BP.compile_blueprint(bp,warnings_as_errors=True)
  assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE,path
  cdo=ue.get_default_object(bp.generated_class())
  flags={name:ue.SystemLibrary.does_implement_interface(cdo,cls) for name,cls in interfaces.items()}
  if not bp.get_name().endswith('InputProbe'):
   assert flags['BPI_RoundReset'] and flags['BPI_Interactable'],(path,flags)
   assert cdo.get_editor_property('replicates') and cdo.get_editor_property('always_relevant'),path
  graphs={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
  text='\n'.join(graphs.values())
  assert not any(n in text for n in ['GetPlayerCharacter','GetPlayerController','GetPlayerPawn']),path
  assert not any(n in text for n in ['Class|BPCoopGameState|SetRoundState','SetwithNotifyRoundState','CallFunction|SetRoundPhase','Class|BPCoopGameMode|SetRoundPhase']),path
  assert not any(n in text for n in ['BPCarryable','ACCarrying','RecordInstant','RecordBegin','RecordEnd']),path
  report['assets'].append({'asset':path,'status':str(bp.get_editor_property('status')),'interfaces':flags,'graphs':graphs})
coordinator=ue.get_default_object(ue.load_asset('/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator').generated_class())
assert not coordinator.get_editor_property('AllowFixtureBridge')
assert not list(coordinator.get_editor_property('CrossedPawns'))
assert not list(coordinator.get_editor_property('EnteredPawns'))
scale=coordinator.static_mesh_component.get_editor_property('relative_scale3d')
assert scale.x==scale.y==scale.z==1,(scale.x,scale.y,scale.z)
base=ue.get_default_object(ue.load_asset('/Game/Puzzles/Gauntlet/BP_HCGauntletGateBridge').generated_class())
assert not base.call_method('SupportsLatch')
assert not base.call_method('RequestLatch',args=(3,1))
assert not base.call_method('QueryLatch',args=(3,1))
assert len(report['assets'])==6,len(report['assets'])
report['passed']=True
(HERE/'primary-review.json').write_text(json.dumps(report,indent=2))
ue.log('HC_GAUNTLET_PRIMARY_AUDIT_PASS')
