"""Pure-data layout manifest; never touches Unreal packages."""
import json
from pathlib import Path

def p(c,r,z): return [(c-22)*500-175,(41-r)*500,z*100]
def spots(center): return [[center[0],center[1]+(i-1.5)*150,center[2]+100] for i in range(4)]
first=[[(25,32,0),(25,30,0),(32,30,2.5),(32,28,5),(32,23,-3),(27,23,-3)],[(19,32,0),(19,30,0),(12,30,-.5),(12,28,-1),(12,23,-3),(17,23,-3)],[(28,34,0),(38,34,0),(38,28,-1),(32,28,-1),(24,28,-3),(24,25,-3)],[(16,34,0),(4,34,0),(4,28,5),(12,28,5),(20,28,-3),(20,25,-3)]]
second=[[(24,20,-3),(24,18,-3),(24,15,0),(15,15,2),(15,13,4),(15,11,4),(17,11,4),(23,8,4),(23,3,4),(23,1,5),(20,1,5),(20,-4,6)],[(18,20,-3),(18,18,0),(24,18,3),(29,18,3.5),(29,13,4),(29,11,4),(27,11,4),(21,8,4),(21,3,7),(23,3,10),(25,3,8),(25,-4,6)],[(27,21,-3),(36,21,0),(36,13,6),(29,13,10),(24,13,5),(24,12,4),(26,8,4),(26,6,7),(34,6,10),(34,-6,6),(27,-6,6)],[(17,21,-3),(8,21,-3),(8,13,-2),(15,13,-2),(20,13,1),(20,12,4),(18,8,4),(18,6,2),(10,6,0),(10,0,0),(10,-6,6),(17,-6,6)]]
first_routes=[{'ColorSlot':i,'nodes':[p(*n) for n in path],'width':400,'obstacles':[]} for i,path in enumerate(first)]
second_routes=[{'ColorSlot':i,'nodes':[p(*n) for n in path],'width':400,'obstacles':[]} for i,path in enumerate(second)]
hall=[-175,9250,-300]; relic=[-175,23250,600]
escape=[relic,[1325,23250,600],[3825,23250,600],[18000,23250,600],[18000,20000,510],[18000,15000,370],[18000,10000,225],[18000,5000,80],[18000,0,0],[16000,0,0],[14500,0,0],[11500,0,0],[10000,0,0],[8500,0,0],[5500,0,0],[4000,0,0],[2500,0,0],[1500,0,0],[0,0,0],[-1150,0,0]]
data={'schema_version':1,'units':'cm','coordinate_system':'X east, Y north, Z up; actor positions are floor contact unless checkpoint','maze_translation':[-175,0,0],'source':'Prototypes/CoopCave/Source/CoopProto/CoopPlayground.cpp MakePaths; first Free heights provisional until scene inspection','spawn_spots':[[-1000,y,100] for y in [-225,-75,75,225]],'plates':[[-450,-650,5],[450,-650,5],[-450,650,5],[450,650,5]],'statues':[[-950,-850,0],[-950,850,0]],'altar':[-1150,0,0],'startpad':[800,0,0],'maze_door':[325,1500,0],'maze_mouth':{'center':[325,2250,150],'extent':[150,650,200],'fork_center':[-175,3500,0],'bounds':{'min':[-2925,1500,-50],'max':[2575,4250,550]}},'first_path_starts':[r['nodes'][0][0:2]+[100] for r in first_routes],'first_routes':first_routes,'meeting':{'center':hall,'extent':[2250,1000,700],'doors':[r['nodes'][0] for r in second_routes],'headlamp_locks':[[-1275,9250,-120],[925,9250,-120]],'braziers':[[-725,8750,-300],[375,8750,-300]]},'second_path_starts':[r['nodes'][0][0:2]+[r['nodes'][0][2]+100] for r in second_routes],'second_routes':second_routes,'relic':{'center':relic,'extent':[2250,1000,600],'cage':relic,'key':[relic[0],relic[1],relic[2]+100],'levers':[[-975,23250,600],[625,23250,600]],'escape_ledge':[1325,23250,600]},'checkpoints':{'1':spots([-800,0,0]),'2':[r['nodes'][0][0:2]+[100] for r in first_routes],'3':spots(hall),'4':[r['nodes'][0][0:2]+[r['nodes'][0][2]+100] for r in second_routes],'5':spots([-175,22750,600]),'6':spots([-175,22750,600])},'escape_route':escape,'escape_width':400,'gates':{'G1':[2500,0,0],'G2':[5500,0,0],'G3':[11500,0,0]},'exit_ledge':[18000,0,0],'notes':['HallB at Y15500 is scenery-only and must be divided/bypassed to keep second paths isolated.','Route nodes are navigation intent, not a collision/playability certificate. Free heights must match captured floor surfaces.','Carrier walkway east of maze is proposed continuous 4 m route; cave return X0..18000 unchanged.']}
import gzip
from scene_ops import floor_z,GAPS,source_scene
root=Path(__file__).resolve().parents[4]
capture=source_scene(root)
for routes in (first_routes,second_routes):
    for route in routes:
        floor=capture['components'][318+route['ColorSlot']]
        for node in route['nodes']:node[2]=floor_z(floor,node[0]+175,node[1],node[2])
# Replace shared HallB traversal by four tubes separated vertically by 7 m.
connectors=[]
anchors=[([-3500,14000,400],[500,17000,400]),([3500,14000,400],[-500,17000,400]),([1000,14000,400],[2000,17000,400]),([-1000,14000,400],[-2000,17000,400])]
for i,(entry,exit) in enumerate(anchors):
    floor=capture['components'][318+i]
    for node in (entry,exit):node[2]=floor_z(floor,node[0],node[1],node[2]);node[0]-=175
    height=400+i*700
    south=[entry[0],entry[1]+300,entry[2]]
    north=[exit[0],exit[1]-300,exit[2]]
    nodes=[entry,south,[south[0],south[1],height],[north[0],north[1],height],north,exit]
    connectors.append({'ColorSlot':i,'nodes':nodes,'width':400,'headroom':350,'climbing_required':i>0})
    old=second_routes[i]['nodes']
    replacement=[n for n in old if n[1]<14250]+nodes+[n for n in old if n[1]>16750]
    second_routes[i]['nodes']=[n for index,n in enumerate(replacement) if index==0 or n!=replacement[index-1]]
data['hall_b_connectors']=connectors
data['gaps']=[]
for gap in GAPS:
    g=dict(gap);x,y=g['center'];z=floor_z(capture['components'][318+g['ColorSlot']],x,y,0)
    g['center']=[x-175,y,z];g['pit_floor']=z-350;g['width']=500;g['runup']=600 if g['length']>250 else 0;g['recovery_steps']={'count':9,'rise':39,'tread':50,'orientation':'east within own pit; top joins either landing edge'}
    data['gaps'].append(g)
    routes=data[g['stage']+'_routes']
    routes[g['ColorSlot']]['obstacles'].append({'kind':'walk_jump' if g['length']==200 else 'sprint_jump','center':g['center'],'length':g['length'],'pit_floor':g['pit_floor'],'recovery':'Climbable overlap volume on each landing end'})
for tube in connectors:
    second_routes[tube['ColorSlot']]['obstacles'].append({'kind':'marked_climbing_shaft','nodes':tube['nodes'],'solo':True,'separation':700})
for slot,kind in enumerate(['collapsing_bridge','rolling_boulder','falling_rocks','collapsing_bridge_and_bats']):
    second_routes[slot]['obstacles'].append({'kind':kind,'center':next(g['center'] for g in data['gaps'] if g['stage']=='second' and g['ColorSlot']==slot),'schedule':'replicated server-clock start; SRSequenceResetSchedule on round reset'})
data['small_relic_spots']=[[-5175,8000,floor_z(capture['components'][319],-5000,8000,-200)+80],[9325,5000,floor_z(capture['components'][320],8000,5000,0)+80],[-10675,5000,floor_z(capture['components'][321],-9000,5000,0)+80],[4825,8250,floor_z(capture['components'][318],5000,8250,-200)+80]]
data['maze_door']=[325,1400,0]
data['source']='PR124 connection derived from PR90: source_index preserved, floor heights sampled before new gap/HallB cuts, one X-175 placement translation'
data['connection_door']={'center':[325,1400,200],'open_center':[325,1400,650],'size':[300,35,400],'owner':'core sole adapter, no duplicate entrance barrier'}
data['connection_boundary']={'y':3200,'opening_min_x':175,'opening_max_x':475,'source_pr':124,'world_geometry_owner':'full modified maze in WorldRoute; never stream original ConnectedMaze alongside'}
data['round6_bounds']={'playable_xy_min':[-1500,-1500],'playable_xy_max':[18500,23750],'walkable_floor_z_min':0,'walkable_floor_z_max':600,'nonlethal_maze_pit_floor_z_min':min(g['pit_floor'] for g in data['gaps']),'key_lost_z_threshold':-1700,'chasm_overlap_z_max':-1900,'chasm_bottom_z':-2300,'note':'Key below-1700 is unreachable on Round6 carrier route; no carrier path enters maze recovery pits. XY is conservative containing box, not a claim that every interior point has a floor.'}
data['deadly_chasms']=[{'center':[10600,23250,-2100],'extent':[8000,1200,200],'visible_depth':2000,'tag':'SixRound.DeadlyChasm','region':'East bridge out of relic chamber only'},{'center':[18000,10625,-2100],'extent':[900,12800,200],'visible_depth':2000,'tag':'SixRound.DeadlyChasm','region':'East descending walkway and exit ledge only'}]
data['notes']=['HallB interior cut and four 7m-separated connectors replace the old extra regroup.','Route nodes are navigation intent, not a collision/playability certificate.','Carrier walkway east of maze is proposed continuous 4m route; cave return X0..18000 unchanged.']
Path(__file__).with_name('positions.json').write_text(json.dumps(data,indent=2)+'\n')
