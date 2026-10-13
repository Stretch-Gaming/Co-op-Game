"""Fresh joining-two native start/mining/door regression. No authoring/saves.

Reuse the immutable v6 transaction with explicit checkout/output adaptation.
Natural start-pad owning movement precedes its intact-R1 prerequisites.
"""
import hashlib,json,time,sys,types,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
old=json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_Client','PlayNumberOfClients':2,'RunUnderOneProcess':True}))
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
OUT=QUEUE/'mining-runtime';OUT.mkdir(exist_ok=True)
target=OUT/'completion-completion-joining-2-owner0.json'
assert not target.exists(),'Preserve previous result and select a fresh output directory before rerun'
inventory=ROOT/'Tools/unreal/playable_state/mining/evidence/inventory.json'
(OUT/'inventory.json').write_bytes(inventory.read_bytes())
SOURCE=ROOT/'Tools/unreal/playable_state/mining/executed/acceptance_transaction_v6.py'
original=SOURCE.read_text(encoding='utf-8-sig')
assert original.count("Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')")==1
assert original.count("Path('/tmp/coop-mining')")==1
adapted=original.replace("Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')",'Path('+repr(str(ROOT))+')').replace("Path('/tmp/coop-mining')",'Path('+repr(str(OUT))+')')
report={'passed':False,'checks':[],'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'adapted_sha256':hashlib.sha256(adapted.encode()).hexdigest(),
 'inventory_reference_sha256':hashlib.sha256(inventory.read_bytes()).hexdigest(),
 'adaptation':'Only original ROOT and OUT literals changed; preserved historical inventory copied for its report hash. Native current assets/roster/quotas are independently checked by v6.',
 'fixtures':['Server approach positions before start-pad; owning movement only starts R1','Ghosts isolated from focused mining transaction'],
 'full_mission_acceptance_pending':True}
state={'phase':'warm','at':time.monotonic(),'deadline':time.monotonic()+340,'rt':None}
editor.editor_request_begin_play()
def step(p):state['phase']=p;state['at']=time.monotonic()
def finish(passed,error=None):
    report.update(passed=passed,error=error,phase=state['phase'])
    if state.get('rt'):
        try:state['rt'].cleanup_input()
        except Exception:report.update(passed=False,cleanup_error=traceback.format_exc())
    (QUEUE/'mining-runtime.json').write_text(json.dumps(report,indent=2))
    editor.editor_request_end_play();step('closing')
def tick(delta):
    try:
        age=time.monotonic()-state['at'];worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
        if state['phase']=='closing':
            if not worlds:
                OBJ.set_properties(settings,json.dumps(old));ue.unregister_slate_post_tick_callback(state['handle'])
            return
        assert time.monotonic()<state['deadline'],'Mining wrapper wall deadline'
        if state['phase']=='warm':
            assert age<35,'Possessed mining roster timeout'
            if age<2:return
            C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
            owners=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled() and p.player_state]
            if len(owners)!=2:return
            path=ROOT/'Tools/unreal/six_round/core/tests/runtime.py';code=path.read_text()
            guard="Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')";assert code.count(guard)==1
            module=types.ModuleType('maze_mining_runtime');module.__file__=str(path)
            exec(compile(code.replace(guard,'Path('+repr(str(ROOT))+')'),str(path),'exec'),module.__dict__)
            rt=module.Runtime(2,'joining');state['rt']=rt;assert rt.round()['index']==0 and rt.round()['phase']==0
            pad=rt.actor('Six_StartPad');state['pad']=pad;p=pad.get_actor_location()
            for i in range(2):
                rt.place(i,(p.x+(i-.5)*140,p.y-520,p.z+100));rt.local(i).get_controller().set_control_rotation(ue.Rotator(yaw=90))
            report['network']=rt.world_inventory;step('first_owner');return
        rt=state['rt'];assert rt.ready()
        G=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
        for i,g in enumerate(ue.GameplayStatics.get_all_actors_of_class(rt.server,G)):g.set_actor_location(ue.Vector(60000+i*200,60000,2000),False,True)
        assert all(not rt.dead(i) for i in range(2)),'Live transaction fixture owner died'
        if state['phase']=='first_owner':
            assert age<15,'First owner could not walk onto pad'
            inside=list(state['pad'].get_overlapping_actors());rt.inject(0,'IA_Move',0 if rt.players[0] in inside else ue.Vector(0,1,0))
            if rt.players[0] in inside:
                assert rt.round()['phase']==0;step('incomplete_wait')
        elif state['phase']=='incomplete_wait':
            assert rt.round()['index']==0 and rt.round()['phase']==0 and rt.players[1] not in state['pad'].get_overlapping_actors()
            if age>1:report['checks'].append('Start pad remains Lobby with only one owner');step('last_owner')
        elif state['phase']=='last_owner':
            assert age<15,'Last owner did not start round through owning movement'
            inside=list(state['pad'].get_overlapping_actors());rt.inject(1,'IA_Move',0 if rt.players[1] in inside else ue.Vector(0,1,0))
            if rt.round()['index']==1 and rt.round()['phase']==1:
                assert all(p in state['pad'].get_overlapping_actors() for p in rt.players)
                for i in range(2):rt.inject(i,'IA_Move',0)
                report['checks'].append('Complete team native overlap/hold starts mining R1 with row2');assert rt.round()['row']=='2';step('settle')
        elif state['phase']=='settle' and age>.8:
            scope={'__file__':str(SOURCE),'__name__':'__main__','ARGS':{'players':2,'profile':'joining','case':'completion','owner':0,'rock_owner':1,'timeout':240,'enter_maze':True}}
            exec(compile(adapted,str(SOURCE),'exec'),scope);state['transaction_scope']=scope;step('transaction')
        elif state['phase']=='transaction' and target.exists():
            result=json.loads(target.read_text());report['transaction']=result
            report['checks'].append('Original v6 owning mining/cart/plates/north-door result retained')
            finish(bool(result['passed']),result.get('error'))
    except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':'mining-runtime.json','profile':'two joining clients','original_transaction_unchanged':True}
