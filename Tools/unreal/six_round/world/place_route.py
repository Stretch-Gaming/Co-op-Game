"""Owned additions only; preserved source remains available for later rebakes."""
import json, math, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from authoring import *
guard()
layout=json.loads(Path(__file__).with_name('positions.json').read_text())
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from target_context import open_target
world,target_package,target_path=open_target(ARGS)
tag='SixRoundWorld'
for a in actors.get_all_level_actors():
    if a.actor_has_tag(tag):
        assert a.get_level().get_outermost().get_name()==target_path
        assert actors.destroy_actor(a)
def spawn(cls,label,pos,yaw=0,tags=()):
    a=actors.spawn_actor_from_class(cls,ue.Vector(*pos),ue.Rotator(yaw=yaw))
    assert a and a.get_level().get_outermost().get_name()==target_path
    a.set_actor_label(label); a.set_editor_property('tags',[ue.Name(tag),*[ue.Name(t) for t in tags]])
    a.set_folder_path('Adventure/SixRound')
    return a
def cube(label,pos,size,yaw=0,material='/Game/Shared/Style/MI_Stylized_Rock',tags=()):
    a=spawn(ue.StaticMeshActor,label,pos,yaw,tags)
    a.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'))
    a.static_mesh_component.set_mobility(ue.ComponentMobility.STATIC)
    a.static_mesh_component.set_collision_profile_name('BlockAll')
    a.static_mesh_component.set_material(0,ue.load_asset(material))
    a.set_actor_scale3d(ue.Vector(*(v/100 for v in size)))
    return a
def segment(label,a,b,width=400,rails=True):
    dx,dy,dz=[b[i]-a[i] for i in range(3)]
    length=math.sqrt(dx*dx+dy*dy+dz*dz)
    assert length>0 and abs(dz)/max(math.hypot(dx,dy),1)<.35, (label,a,b)
    yaw=math.degrees(math.atan2(dy,dx));pitch=math.degrees(math.atan2(dz,math.hypot(dx,dy)))
    center=[(a[i]+b[i])/2 for i in range(3)];center[2]-=15
    floor=cube(label+'_Floor',center,[length+30,width,30],yaw)
    floor.set_actor_rotation(ue.Rotator(pitch=pitch,yaw=yaw),False)
    if rails:
        nx,ny=-math.sin(math.radians(yaw)),math.cos(math.radians(yaw))
        for side in (-1,1):
            pos=[center[0]+nx*(width/2+15)*side,center[1]+ny*(width/2+15)*side,center[2]+95]
            # Clear the joined floor's turn area; full-length inner rails formed
            # bars across the next leg at90-degree walkway corners.
            rail=cube(label+'_Rail'+str(side),pos,[max(30,length-500),30,160],yaw)
            rail.set_actor_rotation(ue.Rotator(pitch=pitch,yaw=yaw),False)
    return floor
# Read-only production map is not loaded or copied. These isolated test proxies
# follow the published cave dimensions so the return route has a floor during QA.
# Passing here cannot certify the teammate's final cave collision or timber gap.
if ARGS.get('include_test_cave_proxies',True):
    for name,pos,size in [('FirstRoom',[0,0,-15],[3000,3000,30]),('Passage',[2000,0,-15],[1000,400,30]),('PlateHall',[4000,0,-15],[3000,3000,30]),('TrapCorridor',[7000,0,-15],[3000,400,30]),('AltarCavern',[10000,0,-15],[3000,2400,30]),('HauntedHall',[14500,0,-15],[6000,1600,30]),('ExitLedge',[18000,0,-15],[1000,1600,30])]:
        cube('TestCaveProxy_'+name,pos,size,tags=('SixRound.TestProxy',))
if ARGS.get('include_mantle_probe',True):
    cube('TraversalProbe_Mantle',[1100,-950,75],[400,400,150],tags=('SixRound.MantleProbe','SixRound.TestProxy'))
# Northern mouth extension uses delivered X325. Original first-room scenery is preserved.
cube('MazeMouthFloor',[325,2300,-15],[300,1800,30])
for x in (150,500):cube('MazeMouthWall'+str(x),[x,2300,275],[50,1800,550])
# Delivered Y3200 fork has one300cm opening; matching side joins keep paths solo.
for label,x,width in [('West',-1000,2350),('East',1650,2350)]:
    cube('ConnectionJoin_'+label,[x,3200,300],[width,50,600])
# A smooth carrier walkway reaches the east cave ledge; no jumps/climbs required.
exit_index=layout['escape_route'].index(layout['exit_ledge'])
route=layout['escape_route'][:exit_index+1]
walkway_count=len(route)-1
for i,(a,b) in enumerate(zip(route,route[1:])):segment('CarrierWalk_'+str(i),a,b,rails=i>=3)
for i,chasm in enumerate(layout['deadly_chasms']):
    volume=spawn(ue.load_asset('/Game/Hazards/Traps/SixRound/BP_SixRoundChasmVolume').generated_class(),'SixRound_DeadlyChasm_'+str(i),chasm['center'],tags=('SixRound.DeadlyChasm',))
    volume.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(*chasm['extent']))
    cube('DeadlyChasm20mBed_'+str(i),[chasm['center'][0],chasm['center'][1],-2350],[chasm['extent'][0]*2,chasm['extent'][1]*2,50])
def climbwall(label,bottom,top,facing=1,span=350):
    height=abs(top[2]-bottom[2])
    if height<1:return
    center=[bottom[0],bottom[1]+160*facing,(bottom[2]+top[2])/2]
    cube(label,center,[span,40,height],material='/Game/Shared/Style/MI_Stylized_Wood',tags=('Climbable',))
    # End just below the upper walk surface: continued forward input cannot
    # automatically restart a climb after the capsule lands on that surface.
    volume_low=min(bottom[2],top[2])-100
    volume_high=max(bottom[2],top[2])-5
    volume=spawn(ue.load_asset('/Game/Hazards/Maze/BP_ClimbVolume').generated_class(),label+'_ClimbVolume',[bottom[0],bottom[1],(volume_low+volume_high)/2],tags=('Climbable',))
    volume.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(220,240,(volume_high-volume_low)/2))
    # Amber ropes and horizontal handholds mark the climbing face.
    for k in range(int(height//75)+1):
        cube(label+'_Handhold'+str(k),[center[0],center[1]-25*facing,min(bottom[2],top[2])+k*75+30],[80,15,12],material='/Game/Hazards/Art/SixRoundMaze/Materials/MI_SixRound_ClimbAmber',tags=('Climbable',))
for connector in layout['hall_b_connectors']:
    slot=connector['ColorSlot'];nodes=connector['nodes']
    for j,(a,b) in enumerate(zip(nodes,nodes[1:])):
        if abs(a[0]-b[0])+abs(a[1]-b[1])<1:
            climbwall(f'SoloConnector_{slot}_Climb{j}',a,b,1 if j==1 else -1)
        else:
            floor_a,floor_b=list(a),list(b)
            if j==2 and slot>0:
                # Open shaft heads: a solid floor at the shaft center would
                # block ascent from below. Thin lips support native mantle exits.
                distance=math.hypot(b[0]-a[0],b[1]-a[1]);ux,uy=(b[0]-a[0])/distance,(b[1]-a[1])/distance
                floor_a[0]+=ux*200;floor_a[1]+=uy*200
                floor_b[0]-=ux*200;floor_b[1]-=uy*200
                cube(f'SoloConnector_{slot}_EntryLip',[a[0],a[1]+260,a[2]-5],[400,160,10])
                cube(f'SoloConnector_{slot}_ExitLip',[b[0],b[1]-260,b[2]-5],[400,160,10])
            if j==2 and slot==1:
                # North-aligned shaft lips must join a north-aligned corridor;
                # the former diagonal put both lips through its side walls.
                floor_a=[a[0],a[1]+200,a[2]];floor_b=[b[0],b[1]-200,b[2]]
                bend_a=[a[0],a[1]+500,a[2]];bend_b=[b[0],b[1]-500,b[2]]
                for piece,(pa,pb) in enumerate([(floor_a,bend_a),(bend_a,bend_b),(bend_b,floor_b)]):
                    segment(f'SoloConnector_1_2_Bend{piece}',pa,pb)
                for piece,(pa,pb) in enumerate([(a,bend_a),(bend_a,bend_b),(bend_b,b)]):
                    dx,dy=pb[0]-pa[0],pb[1]-pa[1];length=math.hypot(dx,dy);yaw=math.degrees(math.atan2(dy,dx));nx,ny=-dy/length,dx/length;mid=[(pa[k]+pb[k])/2 for k in range(3)]
                    for side in (-1,1):cube(f'SoloConnector_1_2_Bend{piece}_Wall{side}',[mid[0]+nx*215*side,mid[1]+ny*215*side,mid[2]+175],[length+30,30,350],yaw)
                    cube(f'SoloConnector_1_2_Bend{piece}_Roof',[mid[0],mid[1],mid[2]+365],[length+30,430,30],yaw)
                continue
            floor=segment(f'SoloConnector_{slot}_{j}',floor_a,floor_b)
            # Full-height sides and roof prevent crossing between solo channels.
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);yaw=math.degrees(math.atan2(dy,dx))
            nx,ny=-dy/length,dx/length
            mid=[(a[k]+b[k])/2 for k in range(3)]
            enclosure_length=max(30,length-200) if j in (0,4) else length+30
            for side in (-1,1):cube(f'SoloConnector_{slot}_{j}_Wall{side}',[mid[0]+nx*215*side,mid[1]+ny*215*side,mid[2]+175],[enclosure_length,30,350],yaw)
            cube(f'SoloConnector_{slot}_{j}_Roof',[mid[0],mid[1],mid[2]+365],[enclosure_length,430,30],yaw)
# Declared solo platforms replace thin partner-only blocks. Their depth provides
# a real upper surface for the server mantle trace and a safe landing.
for challenge in layout.get('solo_challenges',[]):
    name=challenge['name'];cube(name+'_Platform',challenge['cube_center'],challenge['cube_size'],tags=('Climbable','SixRound.SoloClimb'))
    low=challenge['low'];top=challenge['top_z'];base=challenge['base_z']
    volume=spawn(ue.load_asset('/Game/Hazards/Maze/BP_ClimbVolume').generated_class(),name+'_ClimbVolume',[low[0],low[1],(base-100+top-5)/2],tags=('Climbable',))
    volume.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(220,240,(top-5-(base-100))/2))
    front=challenge['cube_center'][1]-challenge['cube_size'][1]/2
    for k in range(4):
        mark=cube(name+'_Handhold'+str(k),[low[0],front-5,base+30+k*60],[80,15,12],material='/Game/Hazards/Art/SixRoundMaze/Materials/MI_SixRound_ClimbAmber')
        mark.static_mesh_component.set_collision_profile_name('NoCollision')
    segment(name+'_RearRamp',challenge['upper_end'],challenge['ramp_end'],width=500,rails=False)
climbwall('Solo_SplitWall',[4525,3500,-17],[4525,3500,233])
# A raised enclosed perch hides its lock from the hall floor. A player climbs
# the marked rim, then drops100cm onto the broad deck to aim above the rim.
for perch in layout['meeting'].get('perches',[]):
    x,y,z=perch['center'];name='MeetingLockPerch_'+str(perch['slot'])
    cube(name+'_Deck',[x,y,-150],perch['deck_size'])
    for axis in (0,1):
        for side in (-1,1):
            pos=[x,y,-100];pos[axis]+=side*(perch['deck_size'][axis]/2+15)
            size=[perch['deck_size'][0]+60,perch['deck_size'][1]+60,400];size[axis]=30
            cube(name+'_Rim'+str(axis)+str(side),pos,size,tags=('Climbable','SixRound.MeetingPerch'))
    volume=spawn(ue.load_asset('/Game/Hazards/Maze/BP_ClimbVolume').generated_class(),name+'_ClimbVolume',[x,y-365,-105],tags=('Climbable',))
    volume.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(perch['deck_size'][0]/2-20,100,205))
    for k in range(6):
        mark=cube(name+'_Amber'+str(k),[x,y-335,-270+k*60],[100,12,12],material='/Game/Hazards/Art/SixRoundMaze/Materials/MI_SixRound_ClimbAmber')
        mark.static_mesh_component.set_collision_profile_name('NoCollision')
for i,gap in enumerate(layout['gaps']):
    x,y,z=gap['center'];pit=gap['pit_floor'];length=gap['length']+160
    cube('NonlethalPit_'+str(i),[x,y,pit-15],[500,length,30])
    # Independent safe recovery: nine walkable39cm steps remain inside this
    # path's pit, so missing a jump never depends on mantling a thick floor slab.
    for step in range(9):
        step_top=pit+(step+1)*39
        cube(f'NonlethalPit_{i}_RecoveryStep{step}',[x-200+step*50,y,(pit+step_top)/2],[50,gap['length']-20,step_top-pit],material='/Game/Shared/Style/MI_Stylized_Wood')
    for side in (-1,1):cube(f'NonlethalPit_{i}_Wall{side}',[x+side*265,y,(pit+z)/2],[30,length,350])
    # Both landing ends are climbable, so a missed jump costs time and allows retreat.
    for side in (-1,1):climbwall(f'NonlethalPit_{i}_Recovery{side}',[x+180,y+side*(gap['length']/2+40),pit],[x+180,y+side*(gap['length']/2+40),z],span=80)
    if gap['stage']=='second':
        kind=('BP_CollapsingBridge','BP_Boulder','BP_FallingRocks','BP_CollapsingBridge')[gap['ColorSlot']]
        seq=spawn(ue.load_asset('/Game/Hazards/Traps/'+kind).generated_class(),f'SecondSprintSequence_{gap["ColorSlot"]}',[x,y,z],90,tags=('SixRound.ResettableHazard',))
        if kind=='BP_CollapsingBridge':seq.set_editor_property('WarningTime',.45)
        if kind=='BP_Boulder':
            seq.set_editor_property('WarningTime',.8)
            # Safe side nook beside the boulder run, with marked nonlethal recovery.
            cube('BoulderSideNook',[x+325,y+600,z-15],[650,500,30])
        if kind=='BP_FallingRocks':seq.set_editor_property('WarningTime',.4)
        if gap['ColorSlot']==3:
            bats=spawn(ue.load_asset('/Game/Hazards/Maze/BP_BatBurst').generated_class(),'SecondPathBatBurst',[x,y-650,z],90,tags=('SixRound.ResettableHazard',))
            bat_mesh=next(c for c in bats.get_components_by_class(ue.StaticMeshComponent) if 'MovingRock' in c.get_name())
            bat_mesh.set_relative_scale3d(ue.Vector(.35,1.2,.12))
            bat_mesh.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Wood'))
for stage in ('first','second'):
    for path in layout[stage+'_routes']:
        slot=path['ColorSlot']
        for index,pos in enumerate(path['nodes']):
            spawn(ue.TargetPoint,f'{stage}_Route_{slot}_{index}',pos,tags=(f'SixRound.{stage}.Path{slot}.Node{index}',))
        spawn(ue.TargetPoint,f'{stage}_PathStart_{slot}',layout[stage+'_path_starts'][slot],tags=(f'SixRound.{stage}.Start{slot}',))
mouth=spawn(ue.load_asset('/Game/Hazards/Maze/BP_MouthSeal').generated_class(),'SixRound_MouthSeal',[0,0,0],tags=('SixRound.MouthSeal',))
for i,route in enumerate(layout['first_routes']):
    pos=list(route['nodes'][0]);pos[2]+=275
    next_pos=route['nodes'][1]
    dx,dy=next_pos[0]-pos[0],next_pos[1]-pos[1];distance=math.hypot(dx,dy)
    # Seal lies upstream of the checkpoint: taken players never respawn inside it.
    pos[0]-=dx/distance*175;pos[1]-=dy/distance*175
    mouth.set_editor_property('Path'+str(i),ue.Vector(*pos))
    # Seal meshes have their long axis along X, perpendicular to forward.
    mouth.set_editor_property('Yaw'+str(i),math.degrees(math.atan2(dy,dx))-90)
traps=[('Spikes',[2000,0,0]),('Darts',[6200,0,0]),('Swing',[7200,0,0]),('Spikes',[8000,0,0]),('Swing',[14000,0,0]),('Swing',[15500,0,0]),('Spikes',[14800,0,0]),('Darts',[16000,0,0])]
for i,(kind,pos) in enumerate(traps):
    trap=spawn(ue.load_asset('/Game/Hazards/Traps/SixRound/BP_SixRound'+kind).generated_class(),'SixRound_ReturnTrap_'+str(i),pos,tags=('SixRound.ResettableHazard',))
    trap.set_editor_property('CarrierSafe',True)
for stage in ('first','second'):
    for route in layout[stage+'_routes']:
        for j,pos in enumerate(route['nodes'][1:-1]):
            kind=('Spikes','Darts','Swing')[j%3]
            spawn(ue.load_asset('/Game/Hazards/Traps/SixRound/BP_SixRound'+kind).generated_class(),f'SixRound_{stage}_{route["ColorSlot"]}_Trap{j}',pos,tags=('SixRound.ResettableHazard',))
assert ue.EditorLoadingAndSavingUtils.save_packages([target_package],False)
RESULT={'production_untouched':True,'test_cave_proxy':ARGS.get('include_test_cave_proxies',True),'connection_source_pr':124,'return_traps':len(traps),'carrier_walkway_segments':walkway_count,'solo_hall_b_connectors':4,'packages':[target_path],'runtime_acceptance_pending':True,'production_acceptance':False,'pending_checks':['capsule/floor traces','climbing response and missing-jump pit recovery','2/3/4 client path playthrough','carrier return trap timing','PK production map manifest compatibility']}
