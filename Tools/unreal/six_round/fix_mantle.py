"""Primary-only narrow mantle repair; writes exactly two locked Blueprints.

Run after active PIE/test callbacks stop. This evaluates only the selected DSL
expressions from source; it never executes the whole traversal/input builders.
Existing validated trace/break/vector aliases are reused. Blueprint transpilation,
compilation and real client mantle/climb exit remain primary runtime gates.
"""
import ast,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(HERE))
from authoring import *

guard()
def source_dsl(path,function):
 tree=ast.parse(path.read_text(encoding='utf-8-sig'))
 calls=[node.value for node in tree.body if isinstance(node,ast.Expr)
        and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name)
        and node.value.func.id=='write' and len(node.value.args)>=3
        and isinstance(node.value.args[1],ast.Constant) and node.value.args[1].value==function]
 assert len(calls)==1,(path,function,len(calls))
 return eval(compile(ast.Expression(calls[0].args[2]),str(path),'eval'),globals())

traversal_source=HERE/'player/traversal.py'
jump_source=HERE/'finish_inputs.py'
mantle_dsl=source_dsl(traversal_source,'MantleOnServer')
jump_dsl=source_dsl(jump_source,'RequestJump')
assert jump_dsl.index('RequestBoost')<jump_dsl.index('RequestStopClimb')<jump_dsl.index('Character|Jump')
traversal=ue.load_asset('/Game/Player/AC_Traversal');character=ue.load_asset('/Game/Core/BP_CoopCharacter')
assert traversal and character
write(traversal,'MantleOnServer',mantle_dsl)
write(character,'RequestJump',jump_dsl)
save(traversal);save(character)
RESULT={'writes':['/Game/Player/AC_Traversal','/Game/Core/BP_CoopCharacter'],
        'functions':['MantleOnServer','RequestJump'],
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (traversal_source,jump_source)},
        'runtime_acceptance_pending':True,'node_aliases':'Reuses existing LineTraceByChannel/BreakHitResult/MakeVector/Select nodes; actual pins/transpiler validation remains primary.'}
