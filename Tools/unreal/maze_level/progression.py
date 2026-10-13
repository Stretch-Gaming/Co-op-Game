"""HC-only maze progression authoring. No actor placement or level saves.

The primary runs this stage in stopped Unreal, then inspects and tests it.
Native override creation supplies a parent-call node. Keep that node and its
data pins; rewire only execution around the unchanged inherited implementation.
"""
import hashlib, json, re, sys, importlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import context
importlib.reload(context)
from context import *

PARENT='/Game/Core/BP_CoopGameMode'
CHECKPOINT='/Game/Puzzles/Test/SixRound/BP_MazeCheckpoint'
ARRIVAL='/Game/Puzzles/Test/SixRound/BP_HallBArrival'
DOOR='/Game/Puzzles/Test/SixRound/BP_TeamHallDoor'
GS='(Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))'
MG='(Utilities|Casting|CastToBP_SixRoundTestGameMode :Object (Game|GetGameMode))'
STATE='(bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))'
PLAY='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")'
CLEAR='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2")'
FAIL='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")'
EQ=lambda a,b:f'(Utilities|Enum|Equal(Enum) {a} {b})'
HEALTH='/Game/Hazards/AC_Health.AC_Health_C'
ALLOWED={MODE,CHECKPOINT,ARRIVAL,DOOR}

def body_of(dsl, name, parameters=''):
    """Remove only the function envelope; never repair/reinterpret its body."""
    match=re.match(r'\(fn\s+'+re.escape(name)+r'\s+\('+re.escape(parameters)+r'\)',dsl)
    assert match and dsl.rstrip().endswith(')'), (name,'Unexpected baseline signature')
    return dsl[match.end():dsl.rfind(')')]

def data_inputs(node):
    """Stable native input-link receipt, excluding the deliberately rewired exec."""
    result=[]
    for pin in BP._get_node_info(node).input_pins:
        if pin.name.lower()=='execute' or pin.type_id.lower()=='exec':continue
        result.append({'name':pin.name,'type':pin.type_id,'value':str(pin.value),
                       'links':sorted((p.node.get_path_name(),p.index_id,str(p.direction)) for p in pin.connected_pins)})
    return result

def preserved_parent(bp,name):
    graph=override(bp,name);nodes=BP.find_nodes(graph)
    parents=[n for n in nodes if n.get_class().get_name()=='K2Node_CallParentFunction']
    entries=[n for n in nodes if n.get_class().get_name()=='K2Node_FunctionEntry']
    assert len(parents)==len(entries)==1,('Native override must supply one existing parent',name)
    assert all(n.get_class().get_name() in ('K2Node_FunctionEntry','K2Node_FunctionResult','K2Node_CallParentFunction') for n in nodes),('Already authored override; inspect before rerun',name)
    return graph,entries[0],parents[0]

def unlink(pin):
    for other in list(pin.list_connected_pins()):pin.break_single_pin_link(other)

def wire_parent(bp,name,native):
    graph,entry,parent=native;before=data_inputs(parent)
    parent_path=parent.get_path_name()
    def call(helper,x):return BP.create_node(graph,'CallFunction|'+helper,ue.IntPoint(x,0),declaring_class=bp.generated_class())
    unlink(entry.find_then_pin());unlink(parent.find_execute_pin())
    if name=='StartRound':
        prepare=call('PrepareMazeRound',250);finish=call('FinishMazeRoundStart',1000)
        tails=list(parent.find_then_pin().list_connected_pins());unlink(parent.find_then_pin())
        assert entry.find_then_pin().try_create_connection(prepare.find_execute_pin())
        assert prepare.find_then_pin().try_create_connection(parent.find_execute_pin())
        assert parent.find_then_pin().try_create_connection(finish.find_execute_pin())
        for tail in tails:assert finish.find_then_pin().try_create_connection(tail)
        for node in (prepare,finish):assert entry.find_output_pin('Index').try_create_connection(node.find_input_pin('Index'))
    else:
        helper='AllowMazeClearRound' if name=='ClearRound' else 'IsMazeHallResourceRound'
        predicate=call(helper,250)
        branch=BP.create_node(graph,'Utilities|FlowControl|Branch',ue.IntPoint(500,0))
        assert entry.find_then_pin().try_create_connection(predicate.find_execute_pin())
        assert predicate.find_then_pin().try_create_connection(branch.find_execute_pin())
        assert predicate.find_output_pin('Allowed').try_create_connection(branch.find_input_pin('Condition'))
        if name=='ClearRound':assert branch.find_then_pin().try_create_connection(parent.find_execute_pin())
        else:
            monitor=call('MonitorMazeHallResources',750)
            assert branch.find_then_pin().try_create_connection(monitor.find_execute_pin())
            assert branch.find_output_pin('else').try_create_connection(parent.find_execute_pin())
    assert parent.get_path_name()==parent_path and data_inputs(parent)==before,('Parent data links changed',name)
    compile_bp(bp)
    return {'node':parent_path,'type_id':BP._get_node_info(parent).type_id,'data_inputs_before':before,'data_inputs_after':data_inputs(parent)}

def run():
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    baseline=json.loads((QUEUE/'baseline.json').read_text(encoding='utf-8-sig'))
    # Decompiled inherited getter aliases can differ with reflection load order.
    # Parent calls remain native; guard their exact saved bytes (independently
    # matched to HEAD's LFS SHA-256 before this stage), rather than regenerating
    # parent graphs or interpreting an alias difference as a product mutation.
    graph_assets=json.loads((QUEUE/'protected-graph-assets.json').read_text(encoding='utf-8-sig'))
    assert graph_assets=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in graph_assets}
    protected_before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in baseline['protected_sha256']}
    assert protected_before==baseline['protected_sha256'],'Protected baseline bytes changed'
    saved=[];parent_routes={};parent_fingerprints={};native_evidence={}
    original_owned=authoring.owned
    def owned(obj):
        original_owned(obj)
        assert obj.get_path_name().split('.')[0] in ALLOWED,('HC-only stage',obj.get_path_name())
    authoring.owned=owned
    try:
        mode=ue.load_asset(MODE);assert mode
        for name in ('StartRound','ClearRound','PollMeetingLocks','RefreshSixObjective','MonitorSixResources','MonitorEscapeRelic'):
            override(mode,name)
        parents={name:preserved_parent(mode,name) for name in ('StartRound','ClearRound','MonitorSixResources')}
        for n,k,value in [('MazeHallStage','int',0),('MazeHallACleared','bool',False),('MazeHallBCleared','bool',False),
                          ('MazeHallBReached','bool',False),('MazeHallLocks','int',0),('MazeHallLit','int',0),
                          ('MazeHallBeams','int',0),('MazeHallBraziers','int',0),('MazeLiving','int',0),
                          ('MazeFlares','int',0),('MazeActiveFlares','int',0),('MazeFlareUseful','bool',False)]:
            var(mode,n,k,value)
        for n,inputs,outputs in [('PrepareMazeRound',[('Index','int')],[]),('FinishMazeRoundStart',[('Index','int')],[]),
                                ('CommitHallBRegroup',[],[]),('MonitorMazeHallResources',[],[]),
                                ('AllowMazeClearRound',[],[('Allowed','bool')]),('IsMazeHallResourceRound',[],[('Allowed','bool')])]:
            fn(mode,n,inputs,outputs)
        write(mode,'PrepareMazeRound',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (== Index 3) (and (>= (Class|BPCoopGameState|GetPlayerCount :self gs) 2) (<= (Class|BPCoopGameState|GetPlayerCount :self gs) 4)))
    (if (and (== index 2) {EQ('phase',CLEAR)})
     {S('MazeHallACleared','false')} {S('MazeHallBCleared','false')} {S('MazeHallBReached','false')} {S('MazeHallStage','0')})
    (if (and (== index 3) {EQ('phase',FAIL)})
     {S('MazeHallBCleared','false')}
     {S('MazeHallStage',f'(select {V("MazeHallBReached")} 2 (select {V("MazeHallACleared")} 1 0))')}))) (:CastFailed)))''','Index')
        write(mode,'FinishMazeRoundStart',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (== Index 6) (and (== index 6) {EQ('phase',PLAY)}))
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Hazards/Maze/BP_MouthSeal.BP_MouthSeal_C")
     (Class|BPMouthSeal|ResetSeal :self item)))) (:CastFailed)))''','Index')
        write(mode,'AllowMazeClearRound',f'''
 (bind gs {GS} (:then {STATE}
  (return (or (!= index 3) (and {V('MazeHallBReached')} {V('MazeHallBCleared')})))) (:CastFailed (return false)))''')
        write(mode,'IsMazeHallResourceRound',f'''(bind gs {GS} (:then {STATE}
 (return (== index 3))) (:CastFailed (return false)))''')
        write(mode,'PollMeetingLocks',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (== index 3) (and {EQ('phase',PLAY)} (or (== {V('MazeHallStage')} 0) (== {V('MazeHallStage')} 2))))
    {S('MazeHallLocks','0')} {S('MazeHallLit','0')} {S('MazeHallBeams','0')} {S('MazeHallBraziers','0')}
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_CrystalLock.BP_CrystalLock_C")
     (if (Actor|ActorHasTag :self item :Tag (select (== {V('MazeHallStage')} 0) "Maze.HallA" "Maze.HallB"))
      (bind lock (Utilities|Casting|CastToBP_CrystalLock :Object item)
       (:then (Class|BPCrystalLock|RefreshLock :self lock)
        (if (Class|BPCrystalLock|GetEnabled :self lock)
         {S('MazeHallLocks',f'(+ {V("MazeHallLocks")} 1)')}
         (if (Class|BPCrystalLock|GetBrazier :self lock)
          {S('MazeHallBraziers',f'(+ {V("MazeHallBraziers")} 1)')}
          (else {S('MazeHallBeams',f'(+ {V("MazeHallBeams")} 1)')}))
         (if (Class|BPCrystalLock|GetLit :self lock) {S('MazeHallLit',f'(+ {V("MazeHallLit")} 1)')}))) (:CastFailed))))
    (if (and (== {V('MazeHallBeams')} (select (== row "2") 1 2))
     (and (== {V('MazeHallBraziers')} (select (== row "4") 2 1)) (== {V('MazeHallLit')} {V('MazeHallLocks')})))
     (if (== {V('MazeHallStage')} 0)
      {S('MazeHallACleared','true')} {S('MazeHallStage','1')} (Class|BPCoopGameMode|RefreshSixObjective :self self)
      (else (if {V('MazeHallBReached')}
       {S('MazeHallBCleared','true')} {S('MazeHallStage','3')} (Class|BPCoopGameMode|ClearRound :self self))))))) (:CastFailed)))''')
        write(mode,'CommitHallBRegroup',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (== index 3) (and {EQ('phase',PLAY)} (and (== {V('MazeHallStage')} 1) {V('MazeHallACleared')})))
    {S('MazeHallBReached','true')}
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/Rounds/BP_RoundDirector.BP_RoundDirector_C")
     (Class|BPRoundDirector|RegroupRoster :self item :Index 3))
    {S('MazeHallStage','2')} (Class|BPCoopGameMode|RefreshSixObjective :self self))) (:CastFailed)))''')
        write(mode,'RefreshSixObjective',f'''
 (bind gs {GS} (:then {STATE}
  (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Cave")
  (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction
   (select (== index 1) "Mine rocks, fill and push the cart, hold the plates."
    (select (== index 2) "Follow your maze path to meeting hall A."
     (select (== index 3)
      (select (== {V('MazeHallStage')} 0) "Meeting hall A: light its locks together."
       (select (== {V('MazeHallStage')} 1) "The way is open: follow the maze to meeting hall B." "Meeting hall B: light its locks together."))
      (select (== index 4) "Follow the deep maze to the relic chamber."
       (select (== index 5) "Hold the cage and lift the relic." "Carry the relic back through the maze to the starting-room altar."))))))) (:CastFailed))''')
        write(mode,'MonitorMazeHallResources',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (== index 3) (and {EQ('phase',PLAY)} (or (== {V('MazeHallStage')} 0) (== {V('MazeHallStage')} 2))))
    {S('MazeLiving','0')} {S('MazeFlares','0')} {S('MazeActiveFlares','0')}
    (for ps (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self ps))
     (Utilities|IsValid :InputObject pawn (:"Is Valid"
      (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
       (:then (if (not (Class|ACHealth|IsDead :self health))
        {S('MazeLiving',f'(+ {V("MazeLiving")} 1)')}
        (bind tools (Utilities|Casting|CastToAC_Tools :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/Tools/AC_Tools.AC_Tools_C"))
         (:then {S('MazeFlares',f'(+ {V("MazeFlares")} (Class|ACTools|GetFlaresLeft :self tools))')}) (:CastFailed)))) (:CastFailed))) (:"Is Not Valid")))
    (for flare (Actor|GetAllActorsOfClass :ActorClass "/Game/Player/Tools/BP_Flare.BP_Flare_C")
     {S('MazeFlareUseful','false')}
     (if (Class|BPFlare|IsActive :self flare)
      (for lock (Actor|GetAllActorswithTag :Tag (select (== {V('MazeHallStage')} 0) "Maze.HallA" "Maze.HallB"))
       (bind brazier (Utilities|Casting|CastToBP_CrystalLock :Object lock)
        (:then (if (and (Class|BPCrystalLock|GetEnabled :self brazier)
         (and (Class|BPCrystalLock|GetBrazier :self brazier) (<= (Transformation|GetDistanceTo :self flare :OtherActor brazier) 180.0)))
         {S('MazeFlareUseful','true')})) (:CastFailed))))
     (if {V('MazeFlareUseful')} {S('MazeActiveFlares',f'(+ {V("MazeActiveFlares")} 1)')}))
    (if (or (< {V('MazeLiving')} (select (== row "2") 1 2))
     (< (+ {V('MazeFlares')} {V('MazeActiveFlares')}) (select (== row "4") 2 1)))
     (Class|BPCoopGameMode|FailRound :self self)))) (:CastFailed)))''')
        write(mode,'MonitorEscapeRelic',f'''
 (if (Networking|HasAuthority)
  (Class|BPCoopGameMode|CacheRelicHome :self self)
  (bind gs {GS} (:then {STATE}
   (if (and (== index 6) (and {EQ('phase',PLAY)} (not {V('MissionDelivered')})))
    (bind keys (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_KeyRelic.BP_KeyRelic_C"))
    (if (== (Utilities|Array|Length :TargetArray keys) 0) (Class|BPCoopGameMode|RestoreMissingRelic :self self)
     (else (for key keys
      (bind (x y z) (Math|Vector|BreakVector :InVec (Transformation|GetActorLocation :self key)))
      (if (or (< z -1700.0) (or (> z 6000.0) (or (< x -12500.0) (or (> x 12500.0) (or (< y -2500.0) (> y 27000.0))))))
       (Class|BPCoopGameMode|FailRound :self self))))))) (:CastFailed)))''')

        cp=create(CHECKPOINT,ue.load_asset('/Game/Puzzles/BP_Checkpoint').generated_class())
        for slot in range(4):
            comp,_=component(cp,'HallBSpot'+str(slot),ue.SceneComponent)
            # Actor must be authored at HallA center; HallB is 6250cm north, 700 up.
            comp.set_relative_location(ue.Vector(0,(slot-1.5)*150+6250,800),False,False)
        override(cp,'GetSpawnTransform')
        bspots='(select (== Slot 0) '+V('HallBSpot0')+' (select (== Slot 1) '+V('HallBSpot1')+' (select (== Slot 2) '+V('HallBSpot2')+' '+V('HallBSpot3')+')))'
        original=body_of(baseline['graphs']['/Game/Puzzles/BP_Checkpoint']['GetSpawnTransform'],'GetSpawnTransform','Slot')
        write(cp,'GetSpawnTransform',f'''(bind gm {MG} (:then
 (if (Class|BPSixRoundTestGameMode|GetMazeHallBReached :self gm)
  (return (Transformation|GetWorldTransform :self {bspots})) (else {original}))) (:CastFailed {original}))''','Slot')
        arrival=create(ARRIVAL,ue.load_asset('/Game/Puzzles/BP_RegroupVolume').generated_class())
        var(arrival,'MazeAllInside','bool',False);var(arrival,'MazeLivingInside','int',0)
        override(arrival,'PollRegroup')
        write(arrival,'PollRegroup',f'''
 (if (Networking|HasAuthority)
  (bind gm {MG} (:then (bind gs {GS} (:then {STATE}
   (if (and (== index 3) (and {EQ('phase',PLAY)} (== (Class|BPSixRoundTestGameMode|GetMazeHallStage :self gm) 1)))
    {S('MazeAllInside','true')} {S('MazeLivingInside','0')}
    (bind inside (Collision|GetOverlappingActors))
    (for ps (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self ps))
     (Utilities|IsValid :InputObject pawn (:"Is Valid"
      (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
       (:then (if (not (Class|ACHealth|IsDead :self health))
        {S('MazeLivingInside',f'(+ {V("MazeLivingInside")} 1)')}
        (if (not (Utilities|Array|ContainsItem :TargetArray inside :ItemToFind pawn)) {S('MazeAllInside','false')}))) (:CastFailed {S('MazeAllInside','false')}))) (:"Is Not Valid" {S('MazeAllInside','false')})))
    (if (and {V('MazeAllInside')} (> {V('MazeLivingInside')} 0))
     (Class|BPSixRoundTestGameMode|CommitHallBRegroup :self gm)))) (:CastFailed))) (:CastFailed)))''')
        door=create(DOOR,ue.load_asset('/Game/Puzzles/BP_MazeDoor').generated_class())
        var(door,'HallNumber','int',0,editable=True);override(door,'RefreshDoor')
        write(door,'RefreshDoor',f'''
 (if (Networking|HasAuthority)
  (bind gm {MG} (:then (bind gs {GS} (:then {STATE}
   {S('Open',f'(or (== index 6) (select (== {V("HallNumber")} 0) (Class|BPSixRoundTestGameMode|GetMazeHallACleared :self gm) (Class|BPSixRoundTestGameMode|GetMazeHallBCleared :self gm)))')}
   (CallFunction|ApplyDoor)) (:CastFailed))) (:CastFailed)))''')
        # Save only HC Blueprint packages; map placement belongs to the primary.
        for name,native in parents.items():
            native_evidence[name]=wire_parent(mode,name,native)
            parent_routes[name]='preserved_native_parent_node'
        for asset in (mode,cp,arrival,door):save(asset);saved.append(asset.get_path_name().split('.')[0])
        current_mode={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(mode)}
        assert all(current_mode[n]==text for n,text in baseline['graphs'][MODE].items()),'Existing HC child graphs changed'
        for name in parent_routes:
            parent_fingerprints[name]=hashlib.sha256(baseline['graphs'][PARENT][name].encode()).hexdigest()
        assert protected_before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected_before}
        assert graph_assets=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in graph_assets},'Protected parent asset changed'
        report={'saved':saved,'parent_routes':parent_routes,'native_parent_nodes':native_evidence,'parent_graph_sha256':parent_fingerprints,
                'stage_values':{'0':'HallA puzzle','1':'travel to HallB','2':'HallB puzzle','3':'complete'},
                'hall_tags':['Maze.HallA','Maze.HallB'],'checkpoint_actor_origin':[-175,9250,-300],
                'hall_b_center':[-175,15500,400],'native_runtime_pending':True,
                'saved_map_packages':[],'protected_bytes_and_graphs_unchanged':True}
        (QUEUE/'progression.json').write_text(json.dumps(report,indent=2));return report
    finally:authoring.owned=original_owned

RESULT=run()
