"""Prevent a lost escape relic from leaving a living team permanently stuck."""
import sys,json
sys.path.insert(0,str(HERE/'core'))
from common import *
guard()
layout=json.loads((HERE/'world/positions.json').read_text())
route=layout['round6_bounds']
bounds={'min_z':route['key_lost_z_threshold'],'max_z':route['walkable_floor_z_max']+2000,
        'min_x':route['playable_xy_min'][0]-1000,'max_x':route['playable_xy_max'][0]+1000,
        'min_y':route['playable_xy_min'][1]-1000,'max_y':route['playable_xy_max'][1]+1000}
gm=ue.load_asset('/Game/Core/BP_CoopGameMode')
var(gm,'RelicHomeReady','bool',False)
var(gm,'RelicHome','Transform')
for name in ('CacheRelicHome','RestoreMissingRelic','MonitorEscapeRelic','BeginEscapeRelicMonitor'):fn(gm,name)
keys='(Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_KeyRelic.BP_KeyRelic_C")'
write(gm,'CacheRelicHome',f'(if (not {V("RelicHomeReady")}) (for key {keys} {S("RelicHome","(Transformation|GetActorTransform :self key)")} {S("RelicHomeReady","true")}))')
spawn=f'(Game|SpawnActorfromClass :Class "/Game/Puzzles/BP_KeyRelic.BP_KeyRelic_C" :SpawnTransform {V("RelicHome")} :CollisionHandlingOverride "AlwaysSpawn" :Owner self)'
write(gm,'RestoreMissingRelic',f'(if {V("RelicHomeReady")} (bind restored {spawn} (:then (Utilities|IsValid :InputObject restored (:"Is Valid" (CallFunction|FailRound)) (:"Is Not Valid")))))')
conditions=[f'({op} {axis} {float(bounds[key])})' for op,axis,key in [('<','z','min_z'),('>','z','max_z'),('<','x','min_x'),('>','x','max_x'),('<','y','min_y'),('>','y','max_y')]]
outside=conditions[-1]
for condition in reversed(conditions[:-1]):outside=f'(or {condition} {outside})'
scan=f'(for key keys (bind (x y z) (Math|Vector|BreakVector :InVec (Transformation|GetActorLocation :self key))) (if {outside} (CallFunction|FailRound)))'
missing=f'(if (== (Utilities|Array|Length :TargetArray keys) 0) (CallFunction|RestoreMissingRelic) (else {scan}))'
active=f'(and (== index 6) (and {EQ("phase",PLAY)} (not {V("MissionDelivered")})))'
body=f'(if (Networking|HasAuthority) (CallFunction|CacheRelicHome) (bind gs {GS} (:then {STATE} (if {active} (bind keys {keys}) {missing})) (:CastFailed)))'
write(gm,'MonitorEscapeRelic',body)
write(gm,'BeginEscapeRelicMonitor','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "MonitorEscapeRelic" :Time 0.2 :bLooping true))')
event(gm,'ReceiveBeginPlay','BeginEscapeRelicMonitor')
save(gm)
RESULT={'lost_relic_restarts_escape':True,'missing_relic_recreated_from_cached_pedestal':True,'bounds':bounds,'runtime_acceptance_pending':True}
