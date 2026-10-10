import ast,sys,importlib,json
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
from editor_toolset.toolsets.blueprint import _BlueprintCache
from editor_toolset.toolsets.data_table import DataTableTools as DT
ue.load_asset('/Game/Player/S_GhostScaling');table=ue.load_asset('/Game/Player/DT_GhostScaling')
ghost=ue.load_asset('/Game/Player/Ghosts/BP_Ghost');spawner=ue.load_asset('/Game/Player/Ghosts/BP_GhostSpawner')
for bp,name in [(ghost,'ApplyScaling'),(spawner,'SpawnRoundGhosts')]:
 _BlueprintCache.invalidate(bp)
 graph=BP.get_graph(bp,name)
 for node in BP.find_nodes(graph):
  if node.get_class().get_name() not in ('K2Node_FunctionEntry','K2Node_FunctionResult'):BP.delete_node(node)
source=ast.parse((HERE/'build_ghosts.py').read_text(encoding='utf-8-sig'))
for node in source.body:
 if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
  call=node.value
  if isinstance(call.func,ast.Name) and call.func.id=='write' and call.args[1].value in ('ApplyScaling','SpawnRoundGhosts'):
   target=ghost if call.args[1].value=='ApplyScaling' else spawner
   body=eval(compile(ast.Expression(call.args[2]),'<owned row reader>','eval'),globals())
   write(target,call.args[1].value,body)
for bp in (ghost,spawner):save(bp)
RESULT={'official_ghost_rows':json.loads(DT.get_rows(table,['2','3','4'])),'readers_rebuilt_for_official_schema':True}
(QUEUE/'official-ghost-schema.json').write_text(json.dumps(RESULT,indent=2))
