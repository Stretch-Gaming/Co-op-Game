"""Bounded native roster/flare/maze checks. No package writes or gameplay RPC shortcuts."""
import json,math,time,traceback
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
for command in ('t.IdleWhenNotForeground 0','Slate.AllowSlateToSleep 0','Slate.bAllowThrottling 0'):
    ue.SystemLibrary.execute_console_command(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(),command)
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
perf=ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
original=json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
original_perf=json.loads(OBJ.get_properties(perf,['bThrottleCPUWhenNotForeground']))
cases=[('L_Site01',2,'joining'),('L_SixRound_Test',2,'joining'),('L_SixRound_Test',3,'joining'),('L_SixRound_Test',4,'joining'),('L_SixRound_Test',3,'host_split')]
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();F=ue.load_asset('/Game/Player/Tools/BP_Flare').generated_class()
U=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class()
actions={n:ue.load_asset(p) for n,p in {'move':'/Game/Input/Actions/IA_Move','flare':'/Game/Core/Input/IA_ThrowFlare','add':'/Game/Core/Input/IA_AddLocalPlayer'}.items()}
lib=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
report={'passed':False,'cases':[],'method':'Owning Enhanced Input/RPC; normal spawns for controls/flares; disclosed maze approach placement fixture; no asset saves','physical_devices':False}
state={'index':0,'phase':'closed','at':time.monotonic(),'deadline':time.monotonic()+500}

def sub(p):return lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(p.get_controller(),ue.EnhancedInputLocalPlayerSubsystem.static_class()))
def inject(p,role,value):sub(p).inject_input_vector_for_action(actions[role],value if isinstance(value,ue.Vector) else ue.Vector(value,0,0),[],[])
def pawns(w):return list(ue.GameplayStatics.get_all_actors_of_class(w,C))
def clock():return ue.GameplayStatics.get_game_state(state['server']).get_server_world_time_seconds()
def flares(w):return list(ue.GameplayStatics.get_all_actors_of_class(w,F))
def stock(p):return p.get_component_by_class(U).get_editor_property('FlaresLeft')
def step(phase):
    state.update({'phase':phase,'at':time.monotonic()})
    (QUEUE/'qa-progress.json').write_text(json.dumps({'case':state['index'],'phase':phase,'case_info':state.get('case')}))
def write_report():
    (QUEUE/'runtime-qa.json').write_text(json.dumps(report,indent=2))
def cleanup():
    for p in state.get('owners',[]):
        for role in actions:inject(p,role,0)
def finish(error=None):
    report['error']=error;report['passed']=error is None
    cleanup();write_report();editor.editor_request_end_play();step('finish')
def begin():
    name,n,profile=cases[state['index']]
    OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_Client' if profile=='joining' else 'PIE_ListenServer',
        'PlayNumberOfClients':n if profile=='joining' else n-1,'RunUnderOneProcess':True}))
    OBJ.set_properties(perf,json.dumps({'bThrottleCPUWhenNotForeground':False}))
    path='/Game/Maps/L_Site01' if name=='L_Site01' else '/Game/Puzzles/Test/SixRound/L_SixRound_Test'
    assert editor.load_level(path)
    state['case']={'map':name,'players':n,'profile':profile,'checks':[],'flares':[]}
    report['cases'].append(state['case']);state['owners']=[]
    editor.editor_request_begin_play();step('warm')

def verify_flare(a):
    root=a.get_editor_property('FlareRoot');visual=a.get_editor_property('FlareVisual');audio=a.get_editor_property('FlareHiss')
    assert root.static_mesh.get_path_name()=='/Engine/BasicShapes/Cylinder.Cylinder'
    assert not root.get_editor_property('visible')
    assert visual.static_mesh.get_path_name()=='/Game/Player/Art/Flares/SM_HandFlare.SM_HandFlare'
    scale=visual.get_world_transform().scale3d
    assert all(abs(getattr(scale,k)-1)<.01 for k in ('x','y','z')),str(scale)
    center=ue.MathLibrary.transform_location(visual.get_world_transform(),visual.static_mesh.get_bounds().origin)
    assert (center-a.get_actor_location()).length()<2,('visual misaligned',str(center),str(a.get_actor_location()))
    assert a.get_owner() in root.copy_array_of_move_ignore_actors()
    assert audio.get_editor_property('sound').get_path_name()=='/Game/Player/Art/Flares/SFX_Flare_Hiss_Loop.SFX_Flare_Hiss_Loop'
    assert audio.get_editor_property('sound').get_editor_property('looping')
    assert audio.get_editor_property('allow_spatialization') and audio.get_editor_property('override_attenuation')
    assert audio.is_playing(),'Active flare hiss is not playing'
    assert isinstance(visual.get_material(3),ue.MaterialInstanceDynamic)
    assert visual.get_material(3).get_scalar_parameter_value('Burn')>.9
    return {'name':a.get_name(),'owner':a.get_owner().player_state.player_id,'scale':[scale.x,scale.y,scale.z],
            'hiss_playing':audio.is_playing(),'burn_started':a.get_editor_property('BurnStarted'),
            'burn_seconds':a.get_editor_property('BurnSeconds')}

def tick(delta):
    try:
        now=time.monotonic();worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
        if state['phase']=='finish':
            if not worlds:
                OBJ.set_properties(settings,json.dumps(original));OBJ.set_properties(perf,json.dumps(original_perf))
                ue.unregister_slate_post_tick_callback(state['handle'])
            return
        assert now<state['deadline'],'Runtime matrix timeout'
        if state['phase']=='closed':
            if not worlds:begin()
            return
        case=state['case'];elapsed=now-state['at']
        if state['phase']=='warm':assert elapsed<20,'PIE roster did not start; inspect editor tick/throttle state'
        if state['phase']=='warm' and elapsed>2 and worlds:
            servers=[w for w in worlds if ue.GameplayStatics.get_game_mode(w)]
            if len(servers)!=1:return
            server=servers[0];owners=[p for w in worlds for p in pawns(w) if p.is_locally_controlled() and p.player_state]
            if case['profile']=='host_split' and len(owners)==case['players']-1:
                state['server']=server;state['owners']=owners
                host=next(p for p in owners if p.get_world()==server);state['host']=host
                step('add');return
            if len(owners)!=case['players'] or len(pawns(server))!=case['players']:return
            state.update({'server':server,'worlds':worlds,'owners':sorted(owners,key=lambda p:p.player_state.player_id)})
            assert all(p.call_method('CanAcceptSixInput') for p in owners)
            state['positions']={p.player_state.player_id:p.get_actor_location() for p in pawns(server)}
            for p in owners:p.get_controller().set_control_rotation(ue.Rotator(yaw=0))
            step('move');return
        if state['phase']=='add':
            inject(state['host'],'add',1 if elapsed<.15 else 0)
            if elapsed>1:
                assert len([p for p in pawns(state['server']) if p.is_locally_controlled()])==2,'F5 split creation failed'
                step('warm')
            return
        if state['phase']=='warm':
            assert elapsed<20,'PIE roster did not start; inspect editor tick/throttle state'
            return
        if state['phase']=='move':
            for p in state['owners']:inject(p,'move',ue.Vector(0,1,0) if elapsed<.5 else ue.Vector())
            if elapsed>1:
                for p in pawns(state['server']):assert (p.get_actor_location()-state['positions'][p.player_state.player_id]).length()>10,'Owning movement blocked'
                case['checks'].append('Every input owner moves its own pawn')
                if case['map']=='L_Site01':
                    case['passed']=True;cleanup();editor.editor_request_end_play();state['index']+=1;step('closed');return
                state['baseline']={p.player_state.player_id:stock(p) for p in pawns(state['server'])};assert min(state['baseline'].values())>=1
                state.update({'throw_owner':0,'spent':set(),'flare_names':set()})
                for p in state['owners']:p.get_controller().set_control_rotation(ue.Rotator(pitch=-60,yaw=0))
                step('throw');return
        if state['phase']=='throw':
            p=state['owners'][state['throw_owner']];inject(p,'flare',1 if elapsed<.2 else 0)
            if elapsed>1:
                pid=p.player_state.player_id;state['spent'].add(pid)
                new=[a for a in flares(state['server']) if a.get_name() not in state['flare_names'] and a.get_owner().player_state.player_id==pid]
                assert len(new)==1,'Q must spawn one owner flare'
                record=verify_flare(new[0]);case['flares'].append(record);state['flare_names'].add(new[0].get_name())
                peers=[a for a in flares(p.get_world()) if a.get_name()==new[0].get_name()];assert len(peers)==1
                verify_flare(peers[0])
                for other in pawns(state['server']):assert stock(other)==state['baseline'][other.player_state.player_id]-(other.player_state.player_id in state['spent'])
                state['throw_owner']+=1
                if state['throw_owner']==len(state['owners']):step('burn')
                else:step('throw')
            return
        if state['phase']=='burn':
            first=case['flares'][0]
            age=clock()-first['burn_started']
            if 18.5<=age<19.5 and not state.get('near_end',False):
                assert all(a.call_method('IsActive') for a in flares(state['server']))
                case['checks'].append('Flares remain active near 20 seconds');state['near_end']=True
            if clock()-case['flares'][-1]['burn_started']>=21:
                assert state.get('near_end',False),'Near-expiry observation missed'
                assert all(not(a.get_name() in state['flare_names']) for w in state['worlds'] for a in flares(w)),'Actor/audio cleanup failed'
                case['checks'].append('New model, emissive and looping spatial hiss follow owner stock and burn lifecycle; expired actors removed on peers')
                p=pawns(state['server'])[0];pid=p.player_state.player_id
                owner=next(o for o in state['owners'] if o.player_state.player_id==pid)
                p.set_actor_location(ue.Vector(325,2250,100),False,True);p.character_movement.stop_movement_immediately()
                owner.get_controller().set_control_rotation(ue.Rotator(yaw=90))
                state.update({'walk_owner':owner,'walk_server':p,'near_end':False})
                case['maze_approach_fixture']=[325,2250,100];step('walk');return
            return
        if state['phase']=='walk':
            p=state['walk_server'];inject(state['walk_owner'],'move',ue.Vector(0,1,0))
            if p.get_actor_location().y>3550:
                inject(state['walk_owner'],'move',ue.Vector())
                case['checks'].append('Owning movement crosses the continuous mouth-to-maze fork passage')
                case['passed']=True;cleanup();write_report();editor.editor_request_end_play();state['index']+=1
                if state['index']==len(cases):finish()
                else:step('closed')
            else:assert elapsed<12,('Mouth-to-maze blocked',str(p.get_actor_location()))
    except Exception:
        finish(traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':'runtime-qa.json','cases':cases}
