import sys
sys.path.insert(0,str(HERE))
from authoring import *
pawn=create('/Game/Puzzles/Test/HC3/BP_HC3HealthFixture',unreal.load_asset('/Game/Core/BP_CoopCharacter').generated_class())
proxy=unreal.load_asset('/Game/Puzzles/Recovery/BP_HCReviveTarget') or unreal.EditorAssetLibrary.duplicate_asset('/Game/Puzzles/Test/BP_TestInteractable','/Game/Puzzles/Recovery/BP_HCReviveTarget')
owned(proxy)
for g in BP.list_graphs(proxy):
 if g.get_name() in ['RecordInstant','RecordBegin','RecordEnd','TestStartRound']:BP.remove_function_graph(proxy,g.get_name())
for bp in [pawn,proxy]:
 g=BP.get_graph(bp,'EventGraph')
 for n in BP.find_nodes(g):BP.delete_node(n)
 compile_bp(bp)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([pawn])
