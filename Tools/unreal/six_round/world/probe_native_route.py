"""Owning-input PIE physical probes. Initial approaches only are fixtures.

ARGS: players2/3/4, profile joining/host_split, probe mouth/gap/pit_recovery/climb/mantle/carrier,
player_id explicit; gap stage first/second and ColorSlot; climb ColorSlot1..3.
Requires the core composite test map with living roster and genuine heavy carrier
for carrier mode. This never edits assets or substitutes setter-based movement.
"""
import importlib.util,json,math
from pathlib import Path
import unreal as ue
world_dir=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('six_round_world_native_harness',world_dir/'native_support.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
probe=ARGS['probe'];assert probe in ('mouth','gap','pit_recovery','climb','mantle','carrier','zipline','chasm')
case='-'+str(ARGS.get('stage',''))+'-slot'+str(ARGS.get('ColorSlot',''))
h=native.Harness(ARGS,'world-native-'+probe+case)
assert 'SixRound' in h.server.get_path_name(),'Use the isolated composite test map'
assert 'player_id' in ARGS and ARGS['player_id'] in h.ids,'Choose an actual input owner explicitly'
pid=ARGS['player_id'];pawn=h.pawn(h.server,pid);owner=h.locals[pid]
assert not h.prop(pawn,'health','bDead') and not pawn.get_editor_property('bTakenProtected')
layout=json.loads((world_dir/'positions.json').read_text())
half=pawn.get_component_by_class(ue.CapsuleComponent).get_scaled_capsule_half_height()
state={'max_z':pawn.get_actor_location().z,'jumped':False,'waypoint':1,'waits':0,'diagnostic_samples':set()}
def pos():return pawn.get_actor_location()
def floor_at(x,y,expected):
    hit=ue.SystemLibrary.line_trace_single(h.server,ue.Vector(x,y,expected+250),ue.Vector(x,y,expected-600),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,h.server_pawns,ue.DrawDebugTrace.NONE,True)
    assert hit,('No actual approach floor',x,y,expected)
    return hit.to_dict()['impact_point'].z
def approach(x,y,z,yaw):
    actual=floor_at(x,y,z);h.fixture_place(pid,[x,y,actual+half+4]);h.aim_yaw(pid,yaw)
def released():h.release_all()
if probe=='chasm':
    assert h.round()['phase']==1 and not pawn.call_method('IsCarryingHeavy'),'Use an empty-handed living faller; heavy key-loss/restart is a separate core gate'
    assert any(not h.prop(h.pawn(h.server,other),'health','bDead') for other in h.ids if other!=pid)
    rect=layout['deadly_chasms'][0];h.fixture_place(pid,[rect['center'][0]+rect['extent'][0]-100,rect['center'][1],300])
    h.fixtures[-1]['kind']='initial airborne chasm fixture; gravity and actual overlap cause death'
elif probe=='carrier':
    assert pawn.call_method('IsCarryingHeavy'),'Pick up real relic via normal interaction before carrier geometry probe'
    assert h.round()['index']==6 and h.round()['phase']==1
    state['route']=layout['escape_route'];x,y,z=state['route'][0];approach(x,y,z,0)
elif probe=='zipline':
    assert pawn.call_method('IsCarryingHeavy'),'Zipline heavy gate requires real relic pickup, not a carry-state setter'
    assert h.round()['index']==6 and h.round()['phase']==1
    lines=ue.GameplayStatics.get_all_actors_with_tag(h.server,'SixRound.EscapeZipline');assert len(lines)==1
    line=lines[0];start=line.get_actor_location();end=line.get_editor_property('EndPoint');rotation=line.get_actor_rotation();scale=line.get_actor_scale3d()
    assert isinstance(end,ue.Vector) and max(abs(rotation.pitch),abs(rotation.yaw),abs(rotation.roll))<.01 and max(abs(scale.x-1),abs(scale.y-1),abs(scale.z-1))<.01
    resolved=[start.x+end.x,start.y+end.y,start.z+end.z]
    assert math.dist(resolved,layout['exit_ledge'])<1,'Native local EndPoint must resolve to real exit ledge'
    boards=[c for c in line.get_components_by_class(ue.BoxComponent) if 'BoardVolume' in c.get_name()];assert len(boards)==1
    board=boards[0].get_world_location();length=math.hypot(end.x,end.y);ux,uy=end.x/length,end.y/length
    approach(board.x-ux*350,board.y-uy*350,layout['relic']['escape_ledge'][2],math.degrees(math.atan2(uy,ux)))
    state.update({'line':line,'end':resolved,'attached_observed':False,'last_distance':None});h.hold(pid,'move',ue.Vector(0,1,0))
elif probe=='gap':
    assert not pawn.call_method('IsCarryingHeavy')
    g=next(g for g in layout['gaps'] if g['stage']==ARGS['stage'] and g['ColorSlot']==ARGS['ColorSlot']);state['gap']=g
    x,y,z=g['center'];approach(x,y-(g['length']/2+650 if g['length']>250 else 350),z,90)
    h.hold(pid,'move',ue.Vector(0,1,0))
    if g['length']>250:h.hold(pid,'sprint',1)
elif probe=='pit_recovery':
    g=next(g for g in layout['gaps'] if g['stage']==ARGS['stage'] and g['ColorSlot']==ARGS['ColorSlot']);x,y,z=g['center'];state['gap']=g
    state['route']=[[x-200,y-g['length']/2-30,g['pit_floor']],[x-200,y,g['pit_floor']+39],[x+200,y,z+1],[x+200,y+g['length']/2+160,z]]
    approach(*state['route'][0],90)
elif probe=='climb':
    tube=next(t for t in layout['hall_b_connectors'] if t['ColorSlot']==ARGS['ColorSlot']);bottom,top=tube['nodes'][1:3]
    assert top[2]>bottom[2]+100
    state['top']=top;state['upper_route']=tube.get('upper_walk_nodes',[tube['nodes'][3]]);state['upper_index']=0;state['upper_reached']=[];approach(*bottom,90);h.hold(pid,'climb',1);h.hold(pid,'move',ue.Vector(0,1,0))
elif probe=='mantle':
    ledges=ue.GameplayStatics.get_all_actors_with_tag(h.server,'SixRound.MantleProbe')
    assert len(ledges)==1,'Place optional test-only150cm mantle probe geometry first'
    ledge=ledges[0];location=ledge.get_actor_location();state['ledge_top']=location.z+75
    approach(location.x,location.y-300,0,90);h.hold(pid,'move',ue.Vector(0,1,0))
else:
    assert not pawn.call_method('IsCarryingHeavy')
    state['route']=[[325,1250,0],[325,2300,0],[325,3300,0],[-175,3500,0]]
    approach(325,1250,0,90)
h.transition('native_'+probe)
def tick(delta):
    current=pos();state['max_z']=max(state['max_z'],current.z)
    state['mantle_observed']=state.get('mantle_observed',False) or bool(h.prop(pawn,'traversal','bMantling'))
    h.motion_evidence[pid]={'probe':probe,'max_server_z':state['max_z'],'mantle_observed':state['mantle_observed'],'current_server_z':current.z,'movement_mode':str(pawn.character_movement.movement_mode)}
    if state['jumped'] and probe in ('mantle','climb'):
        for delay in (.05,.2,.6):
            if h.elapsed()-state['jump_at']>=delay and delay not in state['diagnostic_samples']:
                h.mantle_diagnostic(pid,'after jump '+str(delay)+'s');state['diagnostic_samples'].add(delay)
    if probe!='chasm':assert not h.prop(pawn,'health','bDead'),'Native route probe player died; preserve death evidence'
    if probe=='chasm':
        if h.phase=='native_chasm' and h.prop(pawn,'health','bDead'):
            assert current.z<layout['round6_bounds']['chasm_overlap_z_max']+200;h.transition('chasm_peer_death')
        elif h.phase=='chasm_peer_death' and h.elapsed()>.8:
            for world in h.worlds:assert h.prop(h.pawn(world,pid),'health','bDead')
            h.check('real gravity entered lethal chasm and death replicated',{'initial_airborne_fixture':True,'natural_walk_off_guardrails':False,'kill_top_z':layout['round6_bounds']['chasm_overlap_z_max']});h.finish(True)
    elif probe=='gap':
        g=state['gap'];x,y,z=g['center']
        state['sprint_observed']=state.get('sprint_observed',False) or bool(h.prop(pawn,'traversal','bSprinting'))
        if g['length']<=250:assert not h.prop(pawn,'traversal','bSprinting'),'2m gate must use walking speed'
        state['airborne_observed']=state.get('airborne_observed',False) or pawn.character_movement.movement_mode==ue.MovementMode.MOVE_FALLING
        launch_offset=100 if g['length']>250 else 30
        near_edge=y-g['length']/2
        if not state['jumped'] and current.y>=near_edge-launch_offset:
            assert current.y<near_edge,'Probe tick missed the before-edge jump trigger'
            state['launch_fixture']={'kind':'owning-input jump triggered by manifest edge','requested_offset_cm':launch_offset,'actual_before_edge_cm':near_edge-current.y,'position':[current.x,current.y,current.z]}
            h.hold(pid,'jump',1);state['jumped']=True;state['jump_at']=h.elapsed()
        if state['jumped'] and h.elapsed()-state['jump_at']>.12:h.release(pid,'jump')
        assert current.z>g['pit_floor']+half+40,'Jump fell into recoverable pit; jump gate failed'
        if current.y>y+g['length']/2+140 and pawn.character_movement.movement_mode==ue.MovementMode.MOVE_WALKING:
            assert state.get('airborne_observed',False),'Gap crossing must include actual airborne native movement'
            if g['length']>250:assert state.get('sprint_observed',False),'3.5m gate must observe authoritative sprint state'
            released();h.check('native own-input gap crossed and landed',{'length':g['length'],'stage':g['stage'],'ColorSlot':g['ColorSlot'],'max_capsule_z':state['max_z'],'airborne_observed':True,'sprint_observed':state.get('sprint_observed',False),'landing_mode':'Walking','launch_fixture':state['launch_fixture']});h.finish(True)
    elif probe=='zipline':
        assert pawn.call_method('IsCarryingHeavy'),'Heavy relic lost during actual zipline boarding/ride'
        assert abs(pawn.character_movement.max_walk_speed-h.prop(pawn,'traversal','WalkSpeed')*.5)<1,'Heavy carry must retain half walking speed during the ride'
        parent=pawn.get_attach_parent_actor()
        if not state['attached_observed'] and parent:
            assert parent.get_class().get_name()=='BP_ZiplineTrolley_C'
            state['attached_observed']=True;released();h.check('real owning movement entered board volume and trolley attached',{'local_endpoint':state['end']});h.transition('zipline_ride')
        elif state['attached_observed']:
            distance=math.dist([current.x,current.y,current.z-half],state['end'])
            if state['last_distance'] is not None and parent:assert distance<=state['last_distance']+40,'Trolley travelled away from the landing'
            state['last_distance']=distance
            if not parent and distance<350 and pawn.character_movement.movement_mode==ue.MovementMode.MOVE_WALKING:
                if h.phase!='zipline_landing_wait':h.transition('zipline_landing_wait');return
                if h.elapsed()<1.0:return
                for world in h.worlds:
                    peer=h.pawn(world,pid);p=peer.get_actor_location();assert math.hypot(p.x-state['end'][0],p.y-state['end'][1])<400
                    assert bool(peer.call_method('IsCarryingHeavy')) and not peer.get_attach_parent_actor()
                h.check('heavy trolley ride detached and landed near18000 exit endpoint on all peers',{'expected':state['end'],'actual':[current.x,current.y,current.z]});h.finish(True)
    elif probe=='climb':
        if h.phase.startswith('native_') and current.z-half>=state['top'][2]-155:
            # Native mantle exits the open shaft onto its thin upper lip.
            # Keep climb eligibility through the next owning Jump injection.
            h.release(pid,'move');h.release(pid,'sprint');h.transition('climb_exit_request')
        elif h.phase=='climb_exit_request' and h.elapsed()>.12:
            h.mantle_diagnostic(pid,'before climb exit jump');h.hold(pid,'jump',1);h.transition('climb_exit_mantle');state['jumped']=True;state['jump_at']=h.elapsed()
        elif h.phase=='climb_exit_mantle':
            state['mantle_observed']=state.get('mantle_observed',False) or bool(h.prop(pawn,'traversal','bMantling'))
            if h.elapsed()>.12:h.release(pid,'jump');h.release(pid,'climb')
            if state.get('mantle_observed',False) and not h.prop(pawn,'traversal','bMantling') and current.z>=state['top'][2]+half-5:
                target=state['upper_route'][state['upper_index']];h.aim_yaw(pid,math.degrees(math.atan2(target[1]-current.y,target[0]-current.x)))
                h.hold(pid,'move',ue.Vector(0,1,0));h.transition('climb_landing')
        elif h.phase!='climb_landing' and current.z>=state['top'][2]+half-5 and not h.prop(pawn,'traversal','bClimbing'):
            h.release(pid,'climb');target=state['upper_route'][state['upper_index']];h.aim_yaw(pid,math.degrees(math.atan2(target[1]-current.y,target[0]-current.x)));h.hold(pid,'move',ue.Vector(0,1,0));h.transition('climb_landing')
        elif h.phase=='climb_landing':
            assert not h.prop(pawn,'traversal','bClimbing')
            assert current.z>=state['top'][2]+half-25,'Climb left upper landing and fell'
            target=state['upper_route'][state['upper_index']]
            if math.hypot(target[0]-current.x,target[1]-current.y)<65 and pawn.character_movement.movement_mode==ue.MovementMode.MOVE_WALKING:
                state['upper_reached'].append({'target':target,'actual':[current.x,current.y,current.z]});state['upper_index']+=1
                if state['upper_index']==len(state['upper_route']):
                    assert state.get('mantle_observed',False),'Shaft exit must observe native mantling before upper landing'
                    released();h.check('native own-input marked shaft and manifest upper landing crossed',{'top':state['top'],'max_capsule_z':state['max_z'],'upper_route':state['upper_route'],'upper_reached':state['upper_reached']});h.finish(True);return
                target=state['upper_route'][state['upper_index']]
            h.aim_yaw(pid,math.degrees(math.atan2(target[1]-current.y,target[0]-current.x)));h.hold(pid,'move',ue.Vector(0,1,0))
    elif probe=='mantle':
        state['mantle_observed']=state.get('mantle_observed',False) or bool(h.prop(pawn,'traversal','bMantling'))
        if not state['jumped'] and h.elapsed()>.2:
            h.mantle_diagnostic(pid,'before ground mantle jump');h.hold(pid,'jump',1);state['jumped']=True;state['jump_at']=h.elapsed()
        if state['jumped'] and h.elapsed()-state['jump_at']>.12:h.release(pid,'jump')
        if state['mantle_observed'] and current.z>=state['ledge_top']+half-10 and not h.prop(pawn,'traversal','bMantling'):
            if 'landing_started' not in state:
                h.release(pid,'move');state['landing_started']=h.elapsed()
            # The swept target is 10cm above the surface. Let normal gravity
            # settle the capsule before asserting a supported walking landing.
            if pawn.character_movement.movement_mode==ue.MovementMode.MOVE_WALKING and h.elapsed()-state['landing_started']>=.2:
                released();h.check('native own-input150cm mantle reached top',{'top_z':state['ledge_top'],'max_capsule_z':state['max_z'],'mantle_observed':True,'landing_settle_seconds':h.elapsed()-state['landing_started']});h.finish(True)
            elif h.elapsed()-state['landing_started']>1.5:raise AssertionError('Mantle did not settle onto the actual ledge')
    else:
        route=state['route'];target=route[state['waypoint']];dx,dy=target[0]-current.x,target[1]-current.y
        if math.hypot(dx,dy)<75 and abs(current.z-half-target[2])<55 and pawn.character_movement.movement_mode==ue.MovementMode.MOVE_WALKING:
            h.check('native own-input route waypoint',{'index':state['waypoint'],'target':target,'actual':[current.x,current.y,current.z]})
            state['waypoint']+=1
            if state['waypoint']==len(route):released();h.finish(True);return
            target=route[state['waypoint']];dx,dy=target[0]-current.x,target[1]-current.y
        h.aim_yaw(pid,math.degrees(math.atan2(dy,dx)))
        if probe=='carrier':
            assert pawn.call_method('IsCarryingHeavy') and not h.prop(pawn,'traversal','bSprinting') and not h.prop(pawn,'traversal','bClimbing')
            assert abs(pawn.character_movement.max_walk_speed-h.prop(pawn,'traversal','WalkSpeed')*.5)<1,'Carrier return requires actual half walking speed'
            assert abs(current.z-half-target[2])<max(80,abs(route[state['waypoint']-1][2]-target[2])+80),'Carrier fell off sloped path'
            waiting=False
            for trap in ue.GameplayStatics.get_all_actors_with_tag(h.server,'SixRound.ResettableHazard'):
                if not trap.get_class().get_name().startswith('BP_SixRound'):continue
                if not trap.get_editor_property('CarrierSafe'):continue
                tp=trap.get_actor_location();distance=math.hypot(tp.x-current.x,tp.y-current.y)
                if distance<450 and (tp.x-current.x)*dx+(tp.y-current.y)*dy>0:
                    kind=trap.get_editor_property('Kind')
                    if kind==1:waiting=bool(trap.get_editor_property('Danger') or trap.get_editor_property('Warning'))
                    if kind==2:
                        now=ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds()
                        waiting=abs(math.sin((now-trap.get_editor_property('StartTime'))*trap.get_editor_property('SwingSpeed')))<.7
                    if waiting:break
            if waiting:h.release(pid,'move');state['waits']+=1;return
        h.hold(pid,'move',ue.Vector(0,1,0))
RESULT=h.register(tick)
