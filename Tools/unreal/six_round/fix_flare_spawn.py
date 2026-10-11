"""Primary-only narrow downward-flare spawn repair; two locked asset writes.

No full tools builder execution: preserve current view/scaling/beam/projectile
graphs and collision properties. Stop PIE before this script. Native node/pin,
compile and owning downward-Q/Round3 acceptance are primary gates.
"""
import ast,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(HERE))
from authoring import *

guard()
source=HERE/'player/tools.py'
tree=ast.parse(source.read_text(encoding='utf-8-sig'))
def source_dsl(function):
 calls=[n.value for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Name) and n.value.func.id=='write'
        and len(n.value.args)>=3 and isinstance(n.value.args[1],ast.Constant)
        and n.value.args[1].value==function]
 assert len(calls)==1,(function,len(calls))
 return eval(compile(ast.Expression(calls[0].args[2]),str(source),'eval'),globals())
throw=source_dsl('ThrowFlareOnServer');begin=source_dsl('BeginFlare')
assert throw.index('SphereTraceByChannel')<throw.index('SpawnActorfromClass')
assert 'AlwaysSpawn' in throw and ':bTraceComplex false' in throw
assert begin.index('IgnoreActorwhenMoving')<begin.index('SetTimerbyFunctionName')
tools=ue.load_asset('/Game/Player/Tools/AC_Tools');flare=ue.load_asset('/Game/Player/Tools/BP_Flare')
assert tools and flare
write(tools,'ThrowFlareOnServer',throw)
write(flare,'BeginFlare',begin)
save(tools);save(flare)
RESULT={'writes':['/Game/Player/Tools/AC_Tools','/Game/Player/Tools/BP_Flare'],
        'functions':['ThrowFlareOnServer','BeginFlare'],
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'node_risks':['Collision|IgnoreActorwhenMoving menu alias/casing and Actor/bShouldIgnore pins require native catalog validation; underlying UPrimitiveComponent BlueprintCallable API verified in installed UE5.8 header'],
        'runtime_acceptance_pending':True}
