exec(compile((HERE/'build.py').read_text().split('co=ue.load_asset')[0],str(HERE/'build.py'),'exec'),globals())
from editor_toolset.toolsets.actor import ActorTools as AT
path='/Game/Puzzles/Test/HC_RunEnding/'
gm=ue.load_asset(path+'BP_RunEndingFixtureGM') or BP.create(path.rstrip('/'),'BP_RunEndingFixtureGM',ue.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
if 'FixtureCompleteCalls' not in BP.list_variables(gm):BP.add_variable(gm,'FixtureCompleteCalls','int')
fn(gm,'FixtureComplete')
write(gm,'FixtureComplete','''(fn FixtureComplete () (if (Networking|HasAuthority) (Variables|Default|SetFixtureCompleteCalls (+ (Variables|Default|GetFixtureCompleteCalls) 1)) (CallFunction|SetRoundPhase :Phase "NewEnumerator4")))''')
event(gm,'CompleteMap','FixtureComplete')
compile_bp(gm);assert ue.EditorAssetLibrary.save_loaded_asset(gm,False)
(HERE/'fixture-gm.json').write_text(json.dumps({'passed':True,'graph':BP.read_graph_dsl(BP.get_graph(gm,'EventGraph'))},indent=2))
