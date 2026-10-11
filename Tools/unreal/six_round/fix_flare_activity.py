"""Primary-only flare timer execution and IsActive name-collision repair.

Writes only BP_Flare burn helper/wrapper and BeginFlare/EndFlare/RefreshFlare. Does not change existing
instances, burn duration, projectile properties or tools/input/stock graphs. Stop
PIE, compile/save through this script, inspect actual timer + expiry exec pins,
then run fresh genuine Q throws. Existing actors with stopped timers cannot
establish acceptance of this saved-class correction.
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
 assert len(calls)==1,function
 return eval(compile(ast.Expression(calls[0].args[2]),str(source),'eval'),globals())
graphs={name:source_dsl(name) for name in ('IsBurningFlare','IsActive','BeginFlare','EndFlare','RefreshFlare')}
body=graphs['RefreshFlare']
assert '(CallFunction|IsBurningFlare)' in body and '(CallFunction|IsActive)' not in body
assert '(CallFunction|EndFlare) (Actor|DestroyActor :self self)' in body
flare=ue.load_asset('/Game/Player/Tools/BP_Flare');assert flare
fn(flare,'IsBurningFlare',outputs=[('Active','bool')])
assert graphs['BeginFlare'].count('SetTimerbyFunctionName')==2
assert graphs['EndFlare'].index('ClearTimerbyFunctionName')<graphs['EndFlare'].index('HasAuthority')
for name,body in graphs.items():write(flare,name,body)
save(flare)
RESULT={'writes':['/Game/Player/Tools/BP_Flare'],'functions':list(graphs),
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'runtime_acceptance_pending':True,
        'remaining_checks':['IsBurningFlare schema has Active bool output; RefreshFlare local call must resolve unique helper; compatibility IsActive delegates to it','Server GS cast success must set BurnStarted then start RefreshFlare timer; nonauthority also starts timer','EndFlare clears timer before authority/light-target conditions; expiry branch chains EndFlare to this actor DestroyActor','Fresh downward Q near19-second active and by21-second server/owner actor+light cleanup']}
