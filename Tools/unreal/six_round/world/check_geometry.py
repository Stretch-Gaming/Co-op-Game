"""Editor collision evidence only. This does not replace client walking/jumping tests."""
import json,math,re,sys,importlib
from pathlib import Path
import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()==ARGS.get('target_map','/Game/Hazards/Test/SixRound/L_WorldRoute_Test')
assert world.get_outermost().get_name() in ('/Game/Hazards/Test/SixRound/L_WorldRoute_Test','/Game/Puzzles/Test/SixRound/L_SixRound_Test')
layout=json.loads(Path(__file__).with_name('positions.json').read_text())
sys.path.insert(0,str(Path(__file__).resolve().parent))
import scene_ops;importlib.reload(scene_ops)
captured=scene_ops.scene(ROOT)
character=ue.get_default_object(ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class())
capsule=character.get_component_by_class(ue.CapsuleComponent)
radius=capsule.get_scaled_capsule_radius();half_height=capsule.get_scaled_capsule_half_height()
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()
# Puzzle closures are deliberate game state. Test fixed geometry independently;
# closed doors, live trap schedules and player movement get separate PIE gates.
ignore=[a for a in actors if a.get_class()!=ue.StaticMeshActor.static_class() and not a.get_component_by_class(ue.HierarchicalInstancedStaticMeshComponent)]
report={'passed':False,'capsule_radius':radius,'capsule_half_height':half_height,'sample_spacing':75,'floor_failures':[],'capsule_failures':[],'partition_failures':[],'climb_segments':[],'samples':0,'source_floor_adjustments':0,'method':'Native capsule dimensions; captured floor-following heights and slope support, independent native floor/clearance/partition traces. Does not simulate jump, climb, latency, timing or human play.'}
def capsule_failure(hit,entry):
    data=hit.to_dict() if hit else {};actor=data.get('hit_actor')
    entry['actor']=actor.get_path_name() if actor else None
    entry['actor_label']=actor.get_actor_label() if actor else None
    component=actor.get_component_by_class(ue.StaticMeshComponent) if actor else None
    mesh=component.get_editor_property('static_mesh') if component else None
    entry['mesh']=mesh.get_path_name() if mesh else None
    entry['contact']={}
    for key in ('initial_overlap','start_penetrating','b_start_penetrating','impact_point','location','impact_normal','normal','face_index','penetration_depth','time','distance'):
        if key in data:
            value=data[key]
            entry['contact'][key]=[value.x,value.y,value.z] if all(hasattr(value,k) for k in ('x','y','z')) else value if isinstance(value,(str,int,float,bool,type(None))) else str(value)
    report['capsule_failures'].append(entry)
def gap_at(p):
    for g in layout['gaps']:
        x,y,z=g['center']
        if abs(p[0]-x)<250 and abs(p[1]-y)<g['length']/2:return g
    return None
def floor(name,p,expected):
    hit=ue.SystemLibrary.line_trace_single(world,ue.Vector(p[0],p[1],p[2]+125),ue.Vector(p[0],p[1],p[2]-600),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
    data=hit.to_dict() if hit else {}
    if not hit or abs(data['impact_point'].z-expected)>50:
        actor=data.get('hit_actor')
        report['floor_failures'].append({'route':name,'sample':p,'expected_z':expected,'hit_z':data['impact_point'].z if hit else None,'actor':actor.get_path_name() if actor else None,'label':actor.get_actor_label() if actor else None,'normal_z':data['impact_normal'].z if hit else None})
    return data
def sample_route(name,nodes):
    for i,(a,b) in enumerate(zip(nodes,nodes[1:])):
        transfer=next((c for c in layout.get('solo_challenges',[]) if a==c['virtual_top'] and b==c['landing']),None)
        if transfer:
            low=transfer['low'];top=transfer['top_z']
            wall=ue.SystemLibrary.line_trace_single(world,ue.Vector(low[0],low[1],low[2]+half_height),ue.Vector(low[0],low[1]+180,low[2]+half_height),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
            wall_actor=wall.to_dict()['hit_actor'] if wall else None
            if not wall_actor or not wall_actor.actor_has_tag('SixRound.SoloClimb'):
                report['capsule_failures'].append({'route':name,'sample':low,'actor':None,'kind':'declared_climb_wall_missing'})
            zones=[]
            for actor in actors:
                if actor.get_class().get_name()!='BP_ClimbVolume_C' or not actor.actor_has_tag('Climbable'):continue
                origin,extent=actor.get_actor_bounds(True)
                if abs(origin.x-low[0])<=extent.x+radius and abs(origin.y-low[1])<=extent.y+radius and abs(origin.z-(low[2]+half_height))<=extent.z+half_height:zones.append(actor)
            if not zones:report['capsule_failures'].append({'route':name,'sample':low,'actor':None,'kind':'marked_climb_overlap_missing'})
            start=ue.Vector(a[0],a[1],top+half_height+14);end=ue.Vector(b[0],b[1],top+half_height+14)
            blocked=ue.SystemLibrary.capsule_trace_single(world,start,end,radius,half_height,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
            if blocked:capsule_failure(blocked,{'route':name,'sample':b,'kind':'mantle_transfer_blocked'})
            sample_route(name+'_ClimbLanding',[b,transfer['upper_end']])
            report['climb_segments'].append({'route':name,'height':top-transfer['base_z'],'method':'native wall presence, swept mantle envelope and landing floor; real owning climb input still required','verified_by_trace':True})
            continue
        upper=next((t for t in layout['hall_b_connectors'] if t['ColorSlot']>0 and a==t['nodes'][2] and b==t['nodes'][3]),None)
        if upper:
            entry=[a[0],a[1]+260,a[2]];exit=[b[0],b[1]-260,b[2]];mid=[(a[k]+b[k])/2 for k in range(3)]
            sample_route(name+'_UpperLips',upper.get('upper_walk_nodes',[entry,mid,exit]))
            continue
        distance=math.dist(a,b)
        if distance<.1:continue
        if math.hypot(b[0]-a[0],b[1]-a[1])<1:
            report['climb_segments'].append({'route':name,'segment':i,'height':abs(b[2]-a[2]),'verified_by_trace':False});continue
        count=max(1,math.ceil(distance/75))
        for j in range(count+1):
            p=[a[k]+(b[k]-a[k])*j/count for k in range(3)]
            gap=gap_at(p)
            expected=gap['pit_floor'] if gap else p[2]
            normal_z=1.0
            path=re.fullmatch(r'(first|second)([0-3])',name)
            platform=next((c for c in layout.get('solo_challenges',[]) if path and c['stage']==path[1] and c['ColorSlot']==int(path[2]) and abs(p[0]-c['cube_center'][0])<=c['cube_size'][0]/2 and abs(p[1]-c['cube_center'][1])<=c['cube_size'][1]/2),None)
            ramp=next((c for c in layout.get('solo_challenges',[]) if path and c['stage']==path[1] and c['ColorSlot']==int(path[2]) and abs(p[0]-c['low'][0])<=250 and c['upper_end'][1]<=p[1]<=c['ramp_end'][1]),None)
            if platform and not gap:
                p[2]=platform['top_z'];expected=p[2]
            elif ramp and not gap:
                a_r,b_r=ramp['upper_end'],ramp['ramp_end'];t_r=(p[1]-a_r[1])/(b_r[1]-a_r[1])
                p[2]=a_r[2]+(b_r[2]-a_r[2])*t_r;expected=p[2]
                normal_z=1/math.sqrt(1+((b_r[2]-a_r[2])/(b_r[1]-a_r[1]))**2)
            elif path and not gap:
                # Coarse authored endpoints do not describe the captured ramp's
                # flat corners. Follow the source mesh, never a blocking hit.
                surfaces=[scene_ops.floor_surface(captured['components'][index],p[0]-scene_ops.SHIFT,p[1]) for index in (318+int(path[2]),322)]
                surfaces=[s for s in surfaces if s is not None and abs(s[0]-p[2])<500]
                if surfaces:
                    source_z,normal=max(surfaces,key=lambda s:s[0]);report['source_floor_adjustments']+=abs(source_z-p[2])>1
                    p[2]=source_z;expected=source_z;normal_z=normal[2]
            if gap and gap['center'][0]-225<=p[0]<=gap['center'][0]+225 and abs(p[1]-gap['center'][1])<gap['length']/2-10:
                step=min(9,max(1,int((p[0]-(gap['center'][0]-225))//50)+1))
                expected+=step*39
            data=floor(name,p,expected)
            report['samples']+=1
            if gap:continue
            support=radius*(1/max(normal_z,.1)-1)
            ground=expected
            if data and abs(data['impact_point'].z-expected)<=45 and data['impact_normal'].z>=.7:
                ground=data['impact_point'].z;support=max(support,radius*(1/data['impact_normal'].z-1))
                # A standing body needs support over its whole footprint. These
                # native neighbouring rays admit only published≤45cm steps,
                # never waive a tall obstruction or missing floor.
                for theta in range(0,360,45):
                    dx=radius*math.cos(math.radians(theta));dy=radius*math.sin(math.radians(theta))
                    neighbour=ue.SystemLibrary.line_trace_single(world,ue.Vector(p[0]+dx,p[1]+dy,expected+125),ue.Vector(p[0]+dx,p[1]+dy,expected-100),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
                    if neighbour:
                        z=neighbour.to_dict()['impact_point'].z
                        if expected<=z<=expected+45:ground=max(ground,z)
            center=ue.Vector(p[0],p[1],ground+half_height+4+support)
            hit=ue.SystemLibrary.capsule_trace_single(world,center,center+ue.Vector(0,0,1),radius,half_height,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
            if hit:
                capsule_failure(hit,{'route':name,'sample':p})
sample_route('NorthernMouth',[[325,1400,0],[325,2300,0],[325,3100,0],[325,3300,0],[-175,3500,0]])
for stage in ('first','second'):
    for r in layout[stage+'_routes']:
        if stage=='first':nodes=r['nodes']+r.get('arrival_nodes',[r['nodes'][-1],layout['meeting']['center']])[1:]
        else:nodes=r.get('approach_nodes',[layout['meeting']['center'],r['nodes'][0]])[:-1]+r['nodes']+r.get('arrival_nodes',[r['nodes'][-1],layout['relic']['center']])[1:]
        sample_route(stage+str(r['ColorSlot']),nodes)
sample_route('HeavyCarrier',layout['escape_route'])
report['meeting_perches']=[]
for perch in layout['meeting'].get('perches',[]):
    x,y,z=perch['center'];lock=perch['lock']
    low=perch['front_low']
    front=ue.SystemLibrary.line_trace_single(world,ue.Vector(low[0],low[1],low[2]+half_height),ue.Vector(low[0],low[1]+180,low[2]+half_height),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
    front_actor=front.to_dict()['hit_actor'] if front else None
    if not front_actor or not front_actor.actor_has_tag('SixRound.MeetingPerch'):report['capsule_failures'].append({'route':'MeetingPerch','sample':low,'kind':'marked_rim_missing'})
    rim_z=perch['rim_top_z']+half_height+14
    transfer=ue.SystemLibrary.capsule_trace_single(world,ue.Vector(x,low[1],rim_z),ue.Vector(x,perch['landing'][1],rim_z),radius,half_height,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
    if transfer:capsule_failure(transfer,{'route':'MeetingPerch','sample':perch['landing'],'kind':'rim_transfer_blocked'})
    ground=ue.SystemLibrary.line_trace_single(world,ue.Vector(x,y-800,-150),ue.Vector(*lock),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
    actor=ground.to_dict()['hit_actor'] if ground else None
    hidden=bool(actor and actor.actor_has_tag('SixRound.MeetingPerch'))
    if not hidden:report['capsule_failures'].append({'route':'MeetingPerch','sample':lock,'kind':'lock_visible_from_ground'})
    deck=ue.SystemLibrary.line_trace_single(world,ue.Vector(x,y-175,150),ue.Vector(*lock),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
    deck_actor=deck.to_dict()['hit_actor'] if deck else None
    clear=not deck_actor or not deck_actor.actor_has_tag('SixRound.MeetingPerch')
    if not clear:report['capsule_failures'].append({'route':'MeetingPerch','sample':lock,'kind':'deck_beam_blocked'})
    sample_route('MeetingPerchDeck',[perch['landing'],[x,y-100,0]])
    report['meeting_perches'].append({'slot':perch['slot'],'ground_occluded':hidden,'deck_beam_clear':clear,'climb_input_pending':True})
for tube in layout['hall_b_connectors']:
    if tube.get('upper_walk_nodes'):
        partition_nodes=tube['upper_walk_nodes']
    else:partition_nodes=tube['nodes'][2:4]
    for a,b in zip(partition_nodes,partition_nodes[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
        for j in range(1,10):
            center=[a[k]+(b[k]-a[k])*j/10 for k in range(3)];center[2]+=half_height+4
            for side in (-1,1):
                start=ue.Vector(*center);end=start+ue.Vector(nx*320*side,ny*320*side,0)
                hit=ue.SystemLibrary.capsule_trace_single(world,start,end,radius,half_height,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
                if not hit:report['partition_failures'].append({'ColorSlot':tube['ColorSlot'],'sample':center,'side':side})
report['passed']=not report['floor_failures'] and not report['capsule_failures'] and not report['partition_failures']
report['human_gate_pending']=True
(QUEUE/'world-geometry.json').write_text(json.dumps(report,indent=2))
RESULT={'passed':report['passed'],'samples':report['samples'],'floor_failures':len(report['floor_failures']),'capsule_failures':len(report['capsule_failures']),'partition_failures':len(report['partition_failures']),'climbs_need_client_gate':len(report['climb_segments']),'report':'Saved/SixRound/world-geometry.json','human_gate_pending':True,'production_acceptance':False}
