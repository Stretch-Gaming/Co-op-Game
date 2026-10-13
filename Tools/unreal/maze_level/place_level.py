"""Keep the mining start; retire extra cave rooms and place original meetup puzzles."""
import json,math,sys
sys.path.insert(0,str(HERE))
from context import *
lease(WORLD);lease(PG)
layout=json.loads((QUEUE/'layout.json').read_text())
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level(ENTRY)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();ue.GameplayStatics.flush_level_streaming(world)
levels={l.get_outermost().get_name():l for l in ue.EditorLevelUtils.get_levels(world)}
assert set(levels)=={ENTRY,HC,WORLD,CAVE,PG}
all_actors=list(actors.get_all_level_actors())
def find(label):
    found=[a for a in actors.get_all_level_actors() if a.get_actor_label()==label];assert len(found)==1,(label,len(found));return found[0]
def current(path):assert editor.set_current_level_by_name(path.rsplit('/',1)[-1])
def spawn(path,cls,label,pos,yaw=0,tags=()):
    current(path);cls=ue.load_asset(cls).generated_class() if isinstance(cls,str) else cls
    a=actors.spawn_actor_from_class(cls,ue.Vector(*pos),ue.Rotator(yaw=yaw));assert a and a.get_level().get_outermost().get_name()==path
    a.set_actor_label(label);a.tags=[ue.Name('MazeLevel'),*[ue.Name(t) for t in tags]];a.set_folder_path('MazeLevel');return a
def cube(path,label,pos,size,tags=(),material='/Game/Shared/Style/MI_Stylized_Rock'):
    a=spawn(path,ue.StaticMeshActor,label,pos,tags=tags);a.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'))
    a.static_mesh_component.set_material(0,ue.load_asset(material));a.set_actor_scale3d(ue.Vector(*(n/100 for n in size)));a.static_mesh_component.set_collision_profile_name('BlockAll');return a
assert not any(a.actor_has_tag('MazeLevel.Puzzles') for a in all_actors),'Already placed; inspect before rerun'
removed={CAVE:[],HC:[],PG:[]}
# Prove the normal room is supported independently of the old compound cave loop.
floor=find('Cave_static_000')
ignore=[a for a in all_actors if a!=floor]
floor_samples=[]
for x,y in ((-1000,-225),(800,0),(1450,-200),(1450,200),(325,1000)):
    hit=ue.SystemLibrary.line_trace_single(world,ue.Vector(x,y,150),ue.Vector(x,y,-200),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
    assert hit and abs(hit.to_dict()['impact_point'].z)<5,('Independent starting-room floor missing',x,y)
    floor_samples.append([x,y,hit.to_dict()['impact_point'].z])
cave_exact={'HCA2_CaveSupport','HZ1_Walkway_Ramp','HZA6_DripScatter_05','HZA6_DripScatter_06','Cave_static_006','Cave_static_006_North','Cave_static_006_Lintel'}
outside_prefixes=('HCA2_Light_','HZ1_RelicNook_','HZ1_Gauntlet','HZ1_Chasm_','HZ1_Crystal_','Six_ChasmNorth_',
                  'Round3Start','ExitLedge','MapExit','Torch_Round3Start','Torch_ExitLedge','Torch_MapExit')
global_classes={'DirectionalLight','ExponentialHeightFog','PostProcessVolume','SkyAtmosphere','SkyLight'}
for a in all_actors:
    level=a.get_level().get_outermost().get_name();label=a.get_actor_label();cls=a.get_class().get_name()
    retire=False
    if level==CAVE:
        origin,extent=a.get_actor_bounds(False)
        wholly_outside=(origin.x-extent.x>1800 or origin.x+extent.x<-2200 or origin.y-extent.y>3400 or origin.y+extent.y<-2200)
        retire=label in cave_exact or label.startswith(outside_prefixes) or (wholly_outside and cls not in global_classes)
    elif level==HC:
        retire=label in ('Six_Return_G1','Six_Return_G2','Six_Return_G3')
        pos=a.get_actor_location()
        if cls=='BP_Relic_C' and (pos.x>12500 or (pos.y<3200 and (pos.x>1800 or pos.x<-2200))):retire=True
    elif level==PG:retire=label=='Six_EscapeZipline'
    if retire:removed[level].append(label);assert actors.destroy_actor(a)
assert 'HCA2_CaveSupport' in removed[CAVE]
# Close the retired east opening in the copied room; the north maze door stays.
cube(CAVE,'MazeLevel_StartRoomEastClosure',[1460,0,450],[80,500,900])
# Existing hall A locks stay at their authored perches. Clone their art/data into B.
current(HC)
new_locks=[]
for key in ('headlamp_locks','braziers'):
    for slot in range(2):
        a=find('Six_'+key+'_'+str(slot));assert a.get_level()==levels[HC]
        a.tags=[*a.tags,ue.Name('Maze.HallA'),ue.Name('MazeLevel.Puzzles')]
        clone=actors.duplicate_actor(a,world,ue.Vector(0,6250,700));assert clone and clone.get_level()==levels[HC]
        clone.set_actor_label('Maze_HallB_'+key+'_'+str(slot))
        clone.tags=[t for t in a.tags if str(t)!='Maze.HallA']+[ue.Name('Maze.HallB')]
        assert (clone.get_actor_location()-(a.get_actor_location()+ue.Vector(0,6250,700))).length()<.1
        new_locks.append(clone.get_actor_label())
# Replace CP3 with the HC checkpoint child; only one actor has each round index.
old=find('Six_Checkpoint_3')
cp=spawn(HC,'/Game/Puzzles/Test/SixRound/BP_MazeCheckpoint','Maze_Checkpoint_3',[-175,9250,-300],tags=('Checkpoint3','SixRoundHC','MazeLevel.Puzzles'))
cp.set_editor_property('RoundIndex',3)
for slot in range(4):
    comp=next(c for c in cp.get_components_by_class(ue.SceneComponent) if c.get_name()=='Spot'+str(slot))
    comp.set_relative_location(ue.Vector(0,(slot-1.5)*150,100),False,False)
assert actors.destroy_actor(old);cp.set_actor_label('Six_Checkpoint_3')
cp4=find('Six_Checkpoint_4');third=sorted([r for r in layout['routes'] if r['segment']==2],key=lambda r:r['path'])
base=third[0]['nodes'][0];cp4.set_actor_location(ue.Vector(base[0],base[1],base[2]+100),False,True)
for slot,route in enumerate(third):
    p=route['nodes'][0];comp=next(c for c in cp4.get_components_by_class(ue.SceneComponent) if c.get_name()=='Spot'+str(slot))
    comp.set_relative_location(ue.Vector(p[0]-base[0],p[1]-base[1],p[2]-base[2]),False,False)
arrival=spawn(HC,'/Game/Puzzles/Test/SixRound/BP_HallBArrival','Maze_HallBRegroup',[-175,15500,550],tags=('MazeLevel.Puzzles',))
arrival.set_editor_property('RoundIndex',3);arrival.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(2100,650,300))
# Retire original doors which opened before/after the wrong maze segment.
for slot in range(4):assert actors.destroy_actor(find('Six_PathDoor_'+str(slot)))
doors=[]
for hall,segment in ((0,1),(1,2)):
    for route in sorted([r for r in layout['routes'] if r['segment']==segment],key=lambda r:r['path']):
        p,q=route['nodes'][:2];yaw=math.degrees(math.atan2(q[1]-p[1],q[0]-p[0]))
        a=spawn(HC,'/Game/Puzzles/Test/SixRound/BP_TeamHallDoor',f'Maze_Hall{hall}_Door_{route["path"]}',p,yaw,tags=('MazeLevel.Puzzles',))
        a.set_editor_property('HallNumber',hall);a.set_editor_property('PathSlot',route['path'])
        a.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));a.static_mesh_component.set_relative_scale3d(ue.Vector(.4,6,6))
        a.static_mesh_component.set_relative_location(ue.Vector(0,0,300),False,False);a.static_mesh_component.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock'))
        a.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(350,180,300));doors.append(a.get_actor_label())
# Clear, amber-marked climbing perches for the lamps in both original halls.
amber='/Game/Hazards/Art/SixRoundMaze/Materials/MI_SixRound_ClimbAmber'
for hall,y,z in (('A',9250,-300),('B',15500,400)):
    for slot,x in enumerate((-1275,925)):
        top=z+300
        cube(HC,f'Maze_Hall{hall}_Perch{slot}',[x,y,z+150],[400,400,300],('Climbable','MazeLevel.Puzzles'))
        climb=spawn(HC,'/Game/Hazards/Maze/BP_ClimbVolume',f'Maze_Hall{hall}_Climb{slot}',[x,y-225,z+97.5],tags=('Climbable','MazeLevel.Puzzles'))
        climb.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(220,110,197.5))
        for k in range(5):
            grip=cube(HC,f'Maze_Hall{hall}_Grip{slot}_{k}',[x,y-207,z+45+k*50],[90,12,12],material=amber)
            grip.static_mesh_component.set_collision_profile_name('NoCollision')
        for side in (-1,1):cube(HC,f'Maze_Hall{hall}_PerchRail{slot}_{side}',[x+side*215,y,top+50],[30,400,100])
        cube(HC,f'Maze_Hall{hall}_PerchRailBack{slot}',[x,y+215,top+50],[400,30,100])
# Update only the PG director instance's third-leg anchors, not the Blueprint.
director=find('Six_RoundGhostDirector');assert director.get_level()==levels[PG]
for route in third:
    p=route['nodes'][-3];director.set_editor_property('SecondThreat'+str(route['path']),ue.Vector(p[0],p[1],p[2]+100))
for path in (CAVE,HC,PG):save_level(levels[path])
report={'kept_mining_and_normal_starts':True,'original_meetup_halls':['A','B'],'new_hall_b_locks':new_locks,
    'doors':doors,'checkpoint3_dynamic':True,'checkpoint4_third_paths':True,'removed':removed,
    'independent_start_room_floor_samples':floor_samples,'north_maze_door_preserved':True,'runtime_pending':True}
(QUEUE/'placement.json').write_text(json.dumps(report,indent=2));RESULT=report
