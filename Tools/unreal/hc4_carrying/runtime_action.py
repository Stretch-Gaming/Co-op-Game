"""Runtime fixture driver. Pickup/drop tests inject Enhanced Input, never call RPCs."""
import json,pathlib,time,hashlib,unreal
guard()
ROOT=pathlib.Path(__file__).resolve().parents[3]
opts=json.loads((ROOT/'Saved/HC4/action.json').read_text(encoding='utf-8-sig'))
worlds=sorted(unreal.EditorLevelLibrary.get_pie_worlds(True),key=lambda w:w.get_path_name())
C=unreal.load_asset('/Game/Puzzles/Test/HC4/BP_HC4Character').generated_class()
I=unreal.load_asset('/Game/Puzzles/BP_Carryable').generated_class()
AC=unreal.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
def actor_name(a): return a.get_name() if a else None
def vec(v): return [round(v.x,3),round(v.y,3),round(v.z,3)]
def snapshot():
    rows=[]
    for w in worlds:
        players=unreal.GameplayStatics.get_all_actors_of_class(w,C)
        items=unreal.GameplayStatics.get_all_actors_of_class(w,I)
        rows.append({'world':w.get_path_name(),'server':bool(unreal.GameplayStatics.get_game_mode(w)),
          'plate_weights':[{'probe':b.get_name(),'count':sum(a.actor_has_tag('HC_PlateWeight') for a in b.get_overlapping_actors())} for b in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.TriggerBox) if b.actor_has_tag('HC4_WeightProbe')] if unreal.GameplayStatics.get_game_mode(w) else [],
          'players':[{'name':p.get_name(),'id':p.player_state.get_editor_property('player_id') if p.player_state else None,'local':p.is_locally_controlled(),'position':vec(p.get_actor_location()),'speed':p.character_movement.max_walk_speed,'crouch_speed':p.character_movement.max_walk_speed_crouched,
            'carried':actor_name(p.get_component_by_class(AC).get_editor_property('CarriedItem')),
            'speed_rep':p.get_component_by_class(AC).get_editor_property('CarrySpeed'),
            'input_held':p.get_editor_property('InputHeld'),'focus':actor_name(p.get_editor_property('FocusedTarget')),
            'components':len(p.get_components_by_class(AC)),
            'velocity':vec(p.get_velocity())} for p in players],
          'items':[{'name':i.get_name(),'tags':[str(t) for t in i.tags],'state':i.get_editor_property('CarryState'),'carrier':actor_name(i.get_editor_property('Carrier')),'carrier_id':i.get_editor_property('Carrier').player_state.get_editor_property('player_id') if i.get_editor_property('Carrier') and i.get_editor_property('Carrier').player_state else None,
            'parent':actor_name(i.get_attach_parent_actor()),'collision':str(i.static_mesh_component.get_collision_enabled()),'physics':i.static_mesh_component.is_simulating_physics(),
            'position':vec(i.get_actor_location()),'heavy':i.get_editor_property('Heavy'),'mobility':str(i.static_mesh_component.mobility)} for i in items]})
    return rows
subs=sorted([s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if not s.get_name().startswith('Default__') and s.get_world() in worlds],key=lambda s:(s.get_world().get_path_name(),s.get_path_name()))
clients=[w for w in worlds if not unreal.GameplayStatics.get_game_mode(w)]
server=next(w for w in worlds if unreal.GameplayStatics.get_game_mode(w))
command=opts['command']
if command=='snapshot':
    RESULT={'worlds':snapshot(),'subsystems':[{'path':s.get_path_name(),'world':s.get_world().get_path_name()} for s in subs]}
    if opts.get('label'):
        RESULT['asset_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'Content/Puzzles/BP_Carryable.uasset',ROOT/'Content/Puzzles/Carrying/AC_Carrying.uasset',ROOT/'Content/Puzzles/Test/HC4/BP_HC4Character.uasset']}
        evidence=ROOT/'Tools/unreal/hc4_carrying/evidence'
        evidence.mkdir(exist_ok=True)
        (evidence/(opts['label']+'.json')).write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
elif command=='setup':
    # Arrange the server fixture only; gameplay changes then flow through input/RPCs.
    pawn=sorted(unreal.GameplayStatics.get_all_actors_of_class(server,C),key=lambda p:p.get_name())[opts.get('player',0)]
    item=next(i for i in unreal.GameplayStatics.get_all_actors_of_class(server,I) if opts['tag'] in [str(t) for t in i.tags])
    position=item.get_actor_location()
    guard(); pawn.set_actor_location(unreal.Vector(position.x-150,position.y+opts.get('side',0),95),False,True)
    RESULT={'pawn':pawn.get_name(),'item':item.get_name()}
elif command=='setup_position':
    pawn=sorted(unreal.GameplayStatics.get_all_actors_of_class(server,C),key=lambda p:p.get_name())[opts['player']]
    guard(); pawn.set_actor_location(unreal.Vector(*opts['position']),False,True)
    RESULT={'pawn':pawn.get_name(),'position':opts['position']}
elif command=='aim':
    w=server if opts.get('host') else clients[opts.get('client',0)]
    local=sorted([p for p in unreal.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()],key=lambda p:p.get_name())
    pawn=local[opts.get('local',0)]
    item=next(i for i in unreal.GameplayStatics.get_all_actors_of_class(w,I) if opts['tag'] in [str(t) for t in i.tags])
    # A test-camera override makes aiming deterministic without changing Core.
    guard()
    arm=pawn.get_component_by_class(unreal.SpringArmComponent)
    arm.target_arm_length=0
    camera=pawn.get_component_by_class(unreal.CameraComponent)
    pawn.get_controller().set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),item.get_actor_location()))
    RESULT={'pawn':pawn.get_name(),'camera':vec(camera.get_world_location()),'item':vec(item.get_actor_location())}
elif command=='input':
    chosen=[subs[i] for i in opts.get('subsystems',[0])]
    action=unreal.load_asset(opts['action'])
    assert action
    value=unreal.Vector(*opts.get('value',[1,0,0]))
    duration=opts.get('duration',0.15)
    deadline=time.monotonic()+duration
    handles={'frames':0}
    samples=[]
    started=time.monotonic()
    def inject(delta):
        guard()
        running=handles['frames']<3 or time.monotonic()<deadline
        handles['frames']+=1
        for sub in chosen: sub.inject_input_vector_for_action(action,value if running else unreal.Vector(),[],[])
        if opts.get('record'):
            samples.append({'t':round(time.monotonic()-started,4),'worlds':[{'world':r['world'],'server':r['server'],'players':r['players']} for r in snapshot()]})
        if not running:
            unreal.unregister_slate_post_tick_callback(handles['tick'])
            if opts.get('record'):
                evidence=ROOT/'Tools/unreal/hc4_carrying/evidence';evidence.mkdir(exist_ok=True)
                (evidence/(opts['record']+'.json')).write_text(json.dumps({'samples':samples,'duration':duration,'asset_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'Content/Puzzles/BP_Carryable.uasset',ROOT/'Content/Puzzles/Carrying/AC_Carrying.uasset',ROOT/'Content/Puzzles/Test/HC4/BP_HC4Character.uasset']}},indent=2),encoding='utf-8')
    handles['tick']=unreal.register_slate_post_tick_callback(inject)
    RESULT={'injected':action.get_path_name(),'subsystems':[s.get_path_name() for s in chosen],'duration':duration}
elif command=='rejoin':
    w=clients[opts.get('client',1)]
    pawn=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled())
    guard(); unreal.SystemLibrary.execute_console_command(w,'open 127.0.0.1:17774',pawn.get_controller())
    RESULT={'rejoining':w.get_path_name()}
elif command=='screenshot':
    pawn=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,C) if p.is_locally_controlled())
    target=(ROOT/'Tools/unreal/hc4_carrying/evidence/split_screen.png').as_posix()
    guard(); unreal.SystemLibrary.execute_console_command(server,'HighResShot 1 filename="'+target+'"',pawn.get_controller())
    RESULT={'screenshot':target}
elif command=='authority_check':
    before=snapshot()
    checks=[]
    for w in clients:
        pawn=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled())
        component=pawn.get_component_by_class(AC)
        item=next(i for i in unreal.GameplayStatics.get_all_actors_of_class(w,I) if i.get_editor_property('CarryState')==1)
        guard()
        success=component.call_method('TryPickup',args=(item,))
        component.call_method('DropCarried')
        carried=component.call_method('GetCarried')
        released=component.call_method('ReleaseCarried')
        item_released=item.call_method('ReleaseCarried')
        item.call_method('ResetItem')
        assert success is False and carried is None and released is None and item_released is None
        checks.append({'world':w.get_path_name(),'TryPickup':success,'GetCarried':carried,'ReleaseCarried':released,'item_release':item_released})
    after=snapshot()
    assert [(i['state'],i['carrier_id']) for w in before for i in w['items']]==[(i['state'],i['carrier_id']) for w in after for i in w['items']]
    RESULT={'passed':True,'checks':checks}
    (ROOT/'Tools/unreal/hc4_carrying/evidence/client_authority.json').write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
else: raise AssertionError(command)
