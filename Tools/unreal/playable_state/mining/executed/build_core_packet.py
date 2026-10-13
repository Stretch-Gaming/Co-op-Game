"""Offline packet generator from reviewed source builders, not decompiled DSL."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');OUT=Path('/tmp/coop-mining')
V=lambda n:f'(Variables|Default|Get{n})'
S=lambda n,v:f'(Variables|Default|Set{n} {v})'
I='Index_11_91104438409472A6DD374BADC8DC29B1';P='Phase_15_0B3D934F45B47D0BD2F25CA01264D4DF';A='Attempt_12_246832B34F4E147660E8729696BDD44A';T='PhaseEndsAt_13_75E3D82F49994607AFA23C8B57E08350';R='ScalingRow_14_43C74C304230A92B6620E1A520A230C0'
PLAY='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")';FAIL='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")';LOBBY='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")'
GS='(Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))'
STATE='(bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))'
EQ=lambda a,b:f'(Utilities|Enum|Equal(Enum) {a} {b})'
HEALTH='/Game/Hazards/AC_Health.AC_Health_C'
env=globals().copy()
def source_body(relative,name):
    path=ROOT/relative;tree=ast.parse(path.read_text())
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='write' and len(n.args)>2 and isinstance(n.args[1],ast.Constant) and n.args[1].value==name]
    assert len(calls)==1,(relative,name)
    return eval(compile(ast.Expression(calls[0].args[2]),str(path),'eval'),env)
def expression_end(text,start):
    depth=0;quoted=False;escape=False
    for i in range(start,len(text)):
        c=text[i]
        if quoted:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i+1
    raise AssertionError('Unbalanced builder expression')

monitor=source_body('Tools/unreal/six_round/core/20_rounds.py','SixRoundMonitor')
old=f'(and (== index 1) (< (+ {V("SixLiving")} (select (== row "2") 2 1)) (select (== row "4") 4 3)))'
assert monitor.count(old)==1
monitor=monitor.replace(old,'false')
resource=source_body('Tools/unreal/six_round/core/resource_recovery.py','MonitorSixResources')
marker='(if (== index 1)';start=resource.index(marker);end=expression_end(resource,start)
mine=f'''
 (if (== index 1)
  {S('MiningRocksAvailable','0')} {S('MiningSpawnable','0')}
  {S('MiningActivePlates','0')} {S('MiningUnbroken','0')} {S('MiningPickaxes','0')}
  (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/FirstRoom/BP_MinePickaxe.BP_MinePickaxe_C")
   (bind pick (Utilities|Casting|CastToBP_Carryable :Object item)
    (:then (if (and (>= (.z (Transformation|GetActorLocation :self pick)) -1700.0) (< (Class|BPCarryable|GetCarryState :self pick) 2))
     {S('MiningPickaxes',f'(+ {V("MiningPickaxes")} 1)')})) (:CastFailed)))
  (bind puzzles (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/FirstRoom/BP_MinePuzzle.BP_MinePuzzle_C"))
  (if (== (Utilities|Array|Length :TargetArray puzzles) 1)
   (for item puzzles
    (bind puzzle (Utilities|Casting|CastToBP_MinePuzzle :Object item)
     (:then
      (bind cart (Class|BPMinePuzzle|GetCart :self puzzle))
      (Utilities|IsValid :InputObject cart
       (:"Is Valid"
        (if (> (Class|BPMinePuzzle|GetActiveCount :self puzzle) 0)
         (for deposit (Class|BPMinePuzzle|GetDeposits :self puzzle)
          (Utilities|IsValid :InputObject deposit
           (:"Is Valid" (if (Class|BPMineDeposit|GetActive :self deposit)
            {S('MiningActivePlates',f'(+ {V("MiningActivePlates")} 1)')}
            (if (not (Class|BPMineDeposit|GetBroken :self deposit))
             {S('MiningUnbroken',f'(+ {V("MiningUnbroken")} 1)')}
             (if (> {V('MiningPickaxes')} 0)
              {S('MiningSpawnable',f'(+ {V("MiningSpawnable")} (Class|BPMineDeposit|GetRockCount :self deposit))')}))))
           (:"Is Not Valid")))
         (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/FirstRoom/BP_MineRock.BP_MineRock_C")
          (bind rock (Utilities|Casting|CastToBP_Carryable :Object item)
           (:then (if (and (>= (.z (Transformation|GetActorLocation :self rock)) -1700.0)
            (and (< (Class|BPCarryable|GetCarryState :self rock) 2)
             (not (Utilities|Array|ContainsItem :TargetArray (Class|BPMineCart|GetLoaded :self cart) :ItemToFind item))))
            {S('MiningRocksAvailable',f'(+ {V("MiningRocksAvailable")} 1)')})) (:CastFailed)))
         {S('MiningRemainingQuota','(Math|Integer|Max(Integer) :A (- (Class|BPMineCart|GetRocksNeeded :self cart) (Class|BPMineCart|GetLoadedCount :self cart)) :B 0)')}
         {S('MiningPlateDemand',f'(Math|Integer|Max(Integer) :A (- {V("MiningActivePlates")} {V("SixResourceLiving")}) :B 0)')}
         (if (and (== {V('MiningActivePlates')} (Class|BPMinePuzzle|GetActiveCount :self puzzle))
          (or (and (> {V('MiningUnbroken')} 0) (== {V('MiningPickaxes')} 0))
           (< (+ {V('MiningRocksAvailable')} {V('MiningSpawnable')}) (+ {V('MiningRemainingQuota')} {V('MiningPlateDemand')}))))
          (CallFunction|FailRound))))
       (:"Is Not Valid"))) (:CastFailed)))))
'''
resource=resource[:start]+mine+resource[end:]
reset=f'''
 (if (and (Networking|HasAuthority) {V('WasCheckpointRetry')})
  (bind gs {GS} (:then {STATE}
   (if (and (== index 1) {EQ('phase',PLAY)})
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/FirstRoom/BP_MineCart.BP_MineCart_C")
     (bind cart (Utilities|Casting|CastToBP_MineCart :Object item)
      (:then (Class|BPMineCart|ResetCart :self cart)) (:CastFailed)))
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/FirstRoom/BP_MineDeposit.BP_MineDeposit_C")
     (bind deposit (Utilities|Casting|CastToBP_MineDeposit :Object item)
      (:then (Class|BPMineDeposit|ResetDeposit :self deposit)) (:CastFailed)))
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/FirstRoom/BP_MinePickaxe.BP_MinePickaxe_C")
     (bind pick (Utilities|Casting|CastToBP_Carryable :Object item)
      (:then (Class|BPCarryable|ResetItem :self pick)) (:CastFailed)))
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/FirstRoom/BP_MinePuzzle.BP_MinePuzzle_C")
     (bind puzzle (Utilities|Casting|CastToBP_MinePuzzle :Object item)
      (:then (Class|BPMinePuzzle|SetSolved :self puzzle :Solved false)) (:CastFailed))))) (:CastFailed)))
'''
inventory=json.loads((OUT/'inventory.json').read_text())
retry=json.loads((OUT/'retry-inventory.json').read_text())
gm='/Game/Core/BP_CoopGameMode'
protected=dict(inventory['protected_sha256'])
scenery=[ROOT/'Content/Puzzles/Test/SixRound/L_CaveEnvironment_Test.umap']
for folder in ('Content/Hazards/Art/CavePrototype','Content/Hazards/Blockout'):
    scenery.extend((ROOT/folder).rglob('*.uasset'))
for p in scenery:protected[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
packet={'source_method':'reviewed original source-builder expressions; no decompiler writeback',
        'before':{n:inventory['blueprints'][gm]['graphs'][n] for n in ('SixRoundMonitor','MonitorSixResources','RefreshSixObjective')},
        'retry_before':retry['assets'][gm]['graphs']['RestockAfterCheckpointRetry'],
        'bodies':{'SixRoundMonitor':monitor,'MonitorSixResources':resource,'ResetMiningForCheckpointRetry':reset},
        'new_int_variables':['MiningRocksAvailable','MiningSpawnable','MiningActivePlates','MiningUnbroken','MiningPickaxes','MiningRemainingQuota','MiningPlateDemand'],
        'objectives':[{'asset':gm,'graph':'RefreshSixObjective','old':'The first room: press every plate together.','new':'The first room: mine rocks, fill and push the cart, hold the plates.'},
          {'asset':'/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD','graph':'UpdateSixHUD','old':'Press every plate together.','new':'Mine rocks, push the loaded cart, hold the plates.'},
          {'asset':'/Game/Puzzles/Test/SixRound/BP_PuzzleConnectionDoor','graph':'GetInteractInfo','old':'Solve the first-room plates','new':'Solve the first-room mining puzzle'}],
        'protected_sha256':protected}
(OUT/'core-packet.json').write_text(json.dumps(packet,indent=2))
print('Offline source packet prepared: '+str(OUT/'core-packet.json'))
