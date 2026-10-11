"""Primary-only narrow BeginTrap repair; do not execute the full builder."""
import ast,sys,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import authoring;importlib.reload(authoring)
from authoring import *
guard()
path='/Game/Hazards/Traps/SixRound/BP_SixRoundTrap'
bp=ue.load_asset(path);assert bp and bp.get_path_name().split('.')[0]==path
assert BP.get_graph(bp,'SRTrapConfigureSwingContact'), 'Install swing-contact patch first'
source=Path(__file__).with_name('build_traps.py')
tree=ast.parse(source.read_text(encoding='utf-8-sig'))
calls=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
       and isinstance(n.value.func,ast.Name) and n.value.func.id=='write'
       and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant)
       and n.value.args[1].value=='SRTrapBeginTrap']
assert len(calls)==1,'Exactly one source BeginTrap writer required'
exec(compile(ast.Module(body=calls,type_ignores=[]),str(source),'exec'),globals())
save(bp)
RESULT={'writes':[path],'functions':['SRTrapBeginTrap'],'server':'Configure contact; successful authoritative GameState cast sets StartTime then starts refresh timer in same continuation','client':'Explicit nonauthority branch starts visual refresh timer','runtime_acceptance_pending':True}
