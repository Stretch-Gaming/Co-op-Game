import unreal as ue,json
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
c=ue.load_asset('/Game/Core/BP_CoopCharacter')
(HERE/'post-build-character.json').write_text(json.dumps({g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(c)},indent=2))
