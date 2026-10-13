"""Finite authored obstacle candidates on the immutable PR122 maze; no Unreal writes.

Public API: plan(root) -> JSON-compatible dict. Running this file checks and prints
an offline summary only. Native collision and owning-input play are separate gates.
"""
from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import math

SOURCE = 'SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/connection.json.gz'
SOURCE_SHA256 = '2008b7a684ba0f82d34b97fe259c20ec7abc46e09d00ead5f9c1dd8c6fcbf0ed'
COLORS = ('orange', 'yellow', 'teal', 'purple')
# Exact grid waypoints from CoopPlayground.cpp MakePaths, retaining all three legs.
PATHS = (
    (((25,32),(25,30),(32,30),(32,28),(32,23),(27,23)),
     ((24,20),(24,18),(24,15),(15,15),(15,13),(15,11),(17,11)),
     ((23,8),(23,3),(23,1),(20,1),(20,-4))),
    (((19,32),(19,30),(12,30),(12,28),(12,23),(17,23)),
     ((18,20),(18,18),(24,18),(29,18),(29,13),(29,11),(27,11)),
     ((21,8),(21,3),(23,3),(25,3),(25,-4))),
    (((28,34),(38,34),(38,28),(32,28),(24,28),(24,25)),
     ((27,21),(36,21),(36,13),(29,13),(24,13),(24,12)),
     ((26,8),(26,6),(34,6),(34,-6),(27,-6))),
    (((16,34),(4,34),(4,28),(12,28),(20,28),(20,25)),
     ((17,21),(8,21),(8,13),(15,13),(20,13),(20,12)),
     ((18,8),(18,6),(10,6),(10,0),(10,-6),(17,-6))),
)
DEAD_ROOTS = ((20,0),(12,25),(38,31),(34,0),(4,31),(8,17))
ROOM_SPECS = (
    ('fork',17,33,27,35,0), ('HallA',18,21,26,24,-300),
    ('HallB',18,9,26,11,400), ('relic',18,-8,26,-5,600),
)
RETURN_LEGS = {(0,2), (1,1), (1,0)}
# Each entry is an authored cluster, not an unbounded runtime generator.
# r = low rubble / jump-up rocks; m = amber mantle; w = boulder weave;
# j = 190 cm recoverable walk gap; s = 350 cm recoverable sprint gap.
AUTHORED = (
    (0,0,28,30,'r'), (0,0,32,26,'m'), (0,0,30,23,'w'),
    (0,1,22,15,'r'), (0,1,20,15,'m'), (0,1,17,15,'w'),
    (0,2,23,5,'r'),
    (1,0,16,30,'r'), (1,0,14,23,'m'),
    (1,1,21,18,'r'), (1,1,27,18,'w'), (1,1,29,15,'m'),
    (1,2,21,5,'r'), (1,2,25,1,'w'), (1,2,25,-1,'m'),
    (2,0,36,34,'r'), (2,0,35,28,'j'), (2,0,28,28,'m'),
    (2,1,31,21,'r'), (2,1,36,17,'m'), (2,1,32,13,'w'),
    (2,2,30,6,'r'), (2,2,34,3,'s'), (2,2,34,-3,'m'), (2,2,30,-6,'w'),
    (3,0,11,34,'r'), (3,0,8,28,'j'), (3,0,16,28,'w'),
    (3,1,13,21,'j'), (3,1,8,19,'r'), (3,1,11,13,'m'), (3,1,17,13,'w'),
    (3,2,14,6,'r'), (3,2,10,3,'m'), (3,2,10,-3,'w'), (3,2,14,-6,'r'),
)


def xy(tile):
    return [(tile[0]-22)*500-175, (41-tile[1])*500]


def expand(points):
    out = [points[0]]
    for a, b in zip(points, points[1:]):
        assert a[0] == b[0] or a[1] == b[1]
        dx = (b[0] > a[0]) - (b[0] < a[0])
        dy = (b[1] > a[1]) - (b[1] < a[1])
        while out[-1] != b:
            c, r = out[-1]
            out.append((c+dx, r+dy))
    return out


class Floors:
    """Strict source top-face samples in world space; never invent a fallback Z."""
    def __init__(self, data):
        self.records = {r['source_index']: r for r in data['components']}
        self.triangles = {}
        self.cache = {}
        for index in range(318,323):
            rec = self.records[index]
            assert rec['kind'] == 'procedural'
            assert rec['location'] == [-175.0,0,0]
            assert rec['rotation'] == [0,0,0] and rec['scale'] == [1,1,1]
            triangles = []
            for i in range(0,len(rec['triangles']),3):
                a,b,c = [[v[j]+rec['location'][j] for j in range(3)]
                         for v in (rec['vertices'][k] for k in rec['triangles'][i:i+3])]
                den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den) > 1e-8:
                    triangles.append((a,b,c,den,
                                      min(a[0],b[0],c[0]),max(a[0],b[0],c[0]),
                                      min(a[1],b[1],c[1]),max(a[1],b[1],c[1])))
            self.triangles[index] = triangles

    def at(self, index, x, y, required=True):
        key = (index,round(x,3),round(y,3))
        if key not in self.cache:
            best = None
            for a,b,c,den,x0,x1,y0,y1 in self.triangles[index]:
                if x < x0-.001 or x > x1+.001 or y < y0-.001 or y > y1+.001:
                    continue
                u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
                v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
                if u >= -.00001 and v >= -.00001 and u+v <= 1.00001:
                    z = u*a[2]+v*b[2]+(1-u-v)*c[2]
                    if best is None or z > best:
                        best = z
            self.cache[key] = None if best is None else round(best,3)
        z = self.cache[key]
        assert z is not None or not required, ('No source floor',index,x,y)
        return z


def direction(tiles, i):
    a, b = (tiles[i],tiles[i+1]) if i+1 < len(tiles) else (tiles[i-1],tiles[i])
    return [b[0]-a[0], a[1]-b[1]]


def frame(center, forward, along=0, across=0, z=None):
    return [round(center[0]+forward[0]*along-forward[1]*across,3),
            round(center[1]+forward[1]*along+forward[0]*across,3),
            round(center[2] if z is None else z,3)]


def aabb(center, forward, alo, ahi, tlo, thi, zlo, zhi):
    corners = [frame(center,forward,a,t,z) for a in (alo,ahi)
               for t in (tlo,thi) for z in (zlo,zhi)]
    return {'lo':[min(p[k] for p in corners) for k in range(3)],
            'hi':[max(p[k] for p in corners) for k in range(3)]}


def overlap(a,b):
    return all(a['lo'][k] < b['hi'][k]-.01 and a['hi'][k] > b['lo'][k]+.01 for k in range(3))


def room_geometry():
    result = []
    for name,c0,r0,c1,r1,z in ROOM_SPECS:
        lo,hi = xy((c0,r1)),xy((c1,r0))
        result.append({'name':name,'source_floor':322,
            'center':[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,z],
            'bounds':{'lo':[lo[0]-250,lo[1]-250,z], 'hi':[hi[0]+250,hi[1]+250,z+750]},
            'floor_z':z,'headroom':750,'obstacles_allowed':False})
    return result


def route_data(floors):
    routes = []
    uses = Counter(t for paths in PATHS for points in paths for t in expand(points))
    for path, paths in enumerate(PATHS):
        for segment, points in enumerate(paths):
            tiles = expand(points)
            nodes = [xy(t)+[floors.at(318+path,*xy(t))] for t in tiles]
            corners = [tiles.index(t) for t in points[1:-1]]
            crossings = [i for i,t in enumerate(tiles) if uses[t]>1]
            junctions = [i for i,t in enumerate(tiles) if t in DEAD_ROOTS]
            routes.append({'id':f'{COLORS[path]}_{segment+1}', 'path':path,'segment':segment,
                'color':COLORS[path], 'from':('fork','HallA','HallB')[segment],
                'to':('HallA','HallB','relic')[segment], 'source_floor':318+path,
                'grid_waypoints':[list(t) for t in points], 'tiles':[list(t) for t in tiles],
                'nodes':nodes,'waypoint_nodes':[nodes[tiles.index(t)] for t in points],
                'length_cm':(len(tiles)-1)*500,'width':500,'headroom_nominal':550,
                'corner_indices':corners,'crossing_indices':crossings,
                'junction_indices':junctions,'carrier_return':(path,segment) in RETURN_LEGS,
                'mouth_clearance_cm':1000, 'native_verified':False})
    return routes


def primitive(pid,center,forward,along,across,size,floor,shape='rock',material='rock',tags=()):
    loc = frame(center,forward,along,across,floor+size[2]/2)
    return {'id':pid,'shape':shape,'location':loc,
            'yaw':round(math.degrees(math.atan2(forward[1],forward[0])),3),
            'size':list(size),'material':material,'collision':True,'tags':list(tags),
            'bounds':aabb(loc,forward,-size[0]/2,size[0]/2,-size[1]/2,size[1]/2,
                          loc[2]-size[2]/2,loc[2]+size[2]/2)}


def amber_marks(cluster, piece):
    # Cosmetic marks alone never authorize climbing; the matching overlap zone does.
    c, f = cluster['center'],cluster['forward']
    a = piece['along']-piece['size'][0]/2-4
    t = piece['across']
    result = []
    for i in range(3):
        mark = primitive(f'{piece["id"]}_amber{i}',c,f,a,t,[8,90,12],
                         piece['floor']+30+i*50,'box','amber',('MazeLevel.Amber',))
        mark['collision'] = False
        result.append(mark)
    return result


def add_cluster_pieces(cluster,floors):
    c,f = cluster['center'],cluster['forward']
    safe = cluster['carrier_return']
    kind = cluster['kind']
    # Return clusters put every blocking piece in the opposite shoulder; the
    # untouched source floor is the carrier's lane, never a newly elevated shelf.
    across = 135 if safe else 0
    width = 150 if safe else 430
    if kind == 'rubble_steps':
        specs = [(-280,across,(200,width,35)),(0,across,(220,width,80)),
                 (270,across,(200,width,40))]
    elif kind == 'amber_mantle':
        specs = [(-280,across,(200,width,75)),(40,across,(240,width,150)),
                 (310,across,(160,width,40))]
    else:
        # Weave rocks never span the tunnel. Flat tops allow a faster jump line.
        specs = [(-290,135 if safe else -115,(190,150,85)),
                 (0,135 if safe else 115,(210,150,90)),
                 (290,135 if safe else -115,(190,150,40))]
    for number,(along,t,size) in enumerate(specs):
        pos = frame(c,f,along,t)
        floor = floors.at(cluster['source_floor'],pos[0],pos[1])
        piece = primitive(f'{cluster["id"]}_{number}',c,f,along,t,size,floor)
        piece.update({'along':along,'across':t,'floor':floor})
        cluster['primitives'].append(piece)
        if kind == 'amber_mantle' and number == 1:
            cluster['primitives'] += amber_marks(cluster,piece)
            zone = primitive(f'{piece["id"]}_climb',c,f,along-size[0]/2-45,t,
                             [100,width,165],floor-20,'climb_volume','none',('Climbable',))
            zone['collision'] = False
            zone.update({'overlap':True,'collision_mode':'query_only',
                         'actor_class':'/Game/Hazards/Maze/BP_ClimbVolume.BP_ClimbVolume_C',
                         'note':'Nonblocking overlap, not NoCollision: the server needs capsule overlap.'})
            cluster['primitives'].append(zone)
    cluster['decisions'] = ({'rubble_steps':['step over small rubble','jump onto broad rock','step down'],
                            'amber_mantle':['jump up low rock','climb marked shelf','drop onto landing'],
                            'boulder_weave':['choose shoulder around boulder','jump shortcut or weave','step down']}[kind])
    if safe:
        cluster['decisions'].append('carrier walks uninterrupted left lane')


def make_gap(cluster,floors,length):
    assert not cluster['carrier_return']
    c,f,index = cluster['center'],cluster['forward'],cluster['source_floor']
    runup = 600 if length > 250 else 300
    end = length/2+540
    samples = []
    for a in range(-int(length/2+runup),int(end+100)+1,50):
        p = frame(c,f,a,0)
        samples.append([a,floors.at(index,p[0],p[1])])
    grade = max(abs(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(samples,samples[1:]))
    assert grade <= math.tan(math.radians(5))+.00001, ('Gap slope',cluster['id'],grade)
    pit = min(z for _,z in samples)-285
    last = frame(c,f,end,150)
    exit_z = floors.at(index,last[0],last[1])
    rise = (exit_z-pit)/9
    assert 0 < rise <= 40, ('Recovery stair rise',cluster['id'],rise)
    low,high = min(z for _,z in samples)-110,max(z for _,z in samples)+110
    gap = {'id':cluster['id'],'route':cluster['route'],'path':cluster['path'],
           'segment':cluster['segment'],'center':c,'forward':f,'yaw':cluster['yaw'],
           'source_floor':index,'length':length,'width':440,'runup':runup,'landing':400,
           'floor_grade_degrees':round(math.degrees(math.atan(grade)),3),
           'pit_floor':round(pit,3),'depth_cm':round(c[2]-pit,3),'lethal':False,
           'cuts':[dict(aabb(c,f,-length/2,length/2,-250,250,low,high),purpose='main_gap'),
                   dict(aabb(c,f,length/2-40,end,70,235,low,high),purpose='recovery_stair_channel')],
           'recovery':{'same_path':True,'stairs':9,'rise':round(rise,3),'tread':60,
                       'clear_width':140,'exit':last[:2]+[exit_z],
                       'description':'Side stair channel rejoins forward landing; original floor above stairs is cut.'},
           'native_verified':False,'primitives':[]}
    # Floor extends under the narrow recovery channel, staying inside the original
    # 500 cm corridor footprint; no new room or bridge layer is introduced.
    catch_mid = (end-length/2)/2
    catch_length = end+length/2+100
    gap['primitives'].append(primitive(cluster['id']+'_catch',c,f,catch_mid,0,
                                      [catch_length,440,30],pit-30,'box','rock'))
    for side in (-1,1):
        wall = primitive(cluster['id']+f'_side{side}',c,f,catch_mid,side*235,
                         [catch_length,30,high-pit-80],pit-30,'rock','rock')
        gap['primitives'].append(wall)
    for i in range(9):
        a = length/2+30+i*60
        stair_top = pit+(i+1)*rise
        step = primitive(cluster['id']+f'_stair{i}',c,f,a,150,
                         [60,140,stair_top-pit+30],pit-30,'rock','rock',('MazeLevel.Recovery',))
        gap['primitives'].append(step)
        mark = primitive(cluster['id']+f'_stair_amber{i}',c,f,a,150,
                         [12,100,5],stair_top+.5,'box','amber',('MazeLevel.Amber',))
        mark['collision'] = False
        gap['primitives'].append(mark)
    cluster['decisions'] = ['read marked gap','sprint then jump' if length>250 else 'jump from walk',
                            'miss costs time: recover by same-path stairs']
    cluster['footprint'] = aabb(c,f,-length/2-runup,end+100,-250,250,pit-30,high)
    cluster['primitives'] = gap['primitives']
    return gap


def safe_center(route,i,half_along=400):
    # Rooms/mouths keep 10 m clear; bends, crossed layers and dead-end mouths
    # keep 5 m clear plus the complete obstacle's half-length.
    if min(i,len(route['tiles'])-1-i)*500 < 1000+half_along:
        return False
    reserved = route['corner_indices']+route['crossing_indices']+route['junction_indices']
    return all(abs(i-k)*500 >= 500+half_along for k in reserved)


def return_nodes(routes):
    by = {(r['path'],r['segment']):r for r in routes}
    # Go north into the original hall around the cage lever, then to its mouth.
    result = [[-175,23250,600],[-175,23550,600],[-1175,23550,600]]
    result += list(reversed(by[(0,2)]['nodes']))
    result += [[325,16000,400],[325,15000,400],[1825,15000,400]]
    result += list(reversed(by[(1,1)]['nodes']))
    result += [[-2175,10000,-300],[-2175,9000,-300]]
    result += list(reversed(by[(1,0)]['nodes']))
    result += [[-1675,3500,0],[325,3500,0],[325,3200,0],[325,2250,0],[325,1400,0],[325,750,0],[325,0,0],[-900,205,0],[-1150,205,0]]
    return [p for i,p in enumerate(result) if not i or p != result[i-1]]


def plan(root):
    root = Path(root).resolve()
    source = root/SOURCE
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256, 'Immutable PR122 source changed'
    data = json.loads(gzip.decompress(raw))
    assert len(data['components']) == 563
    assert data['metadata']['maze_offset_x'] == -175
    floors = Floors(data)
    routes = route_data(floors)
    by = {(r['path'],r['segment']):r for r in routes}
    rooms = room_geometry()
    clusters,gaps = [],[]
    names = {'r':'rubble_steps','m':'amber_mantle','w':'boulder_weave','j':'walk_gap','s':'sprint_gap'}
    for number,(p,s,col,row,kind) in enumerate(AUTHORED):
        route = by[(p,s)]
        tile = [col,row]
        i = route['tiles'].index(tile)
        # Gaps have a longer envelope because their recovery niche and run-up
        # must also remain outside corners/crossings/mouths.
        half = 850 if kind=='s' else 800 if kind=='j' else 400
        assert safe_center(route,i,half), ('Authored site in reserved zone',p,s,tile,kind)
        c,f = route['nodes'][i],direction(route['tiles'],i)
        cluster = {'id':f'ML_{COLORS[p]}_{s+1}_{number:02d}', 'route':route['id'],
                   'path':p,'segment':s,'source_floor':318+p,'grid':tile,'tile_index':i,
                   'center':c,'location':c,'forward':f,'yaw':math.degrees(math.atan2(f[1],f[0])),
                   'kind':names[kind],'carrier_return':route['carrier_return'],
                   'height':150 if kind=='m' else 90 if kind=='w' else 80,
                   'footprint':aabb(c,f,-400,400,-215,215,c[2]-110,c[2]+300),
                   'decisions':[],'primitives':[],'native_verified':False}
        if route['carrier_return']:
            cluster['return_safe_lane'] = {'across_min':-100,'across_max':60,'width':160,
                                          'floor':'unchanged source','max_new_step':0,'capsule_radius':35}
        if kind in ('j','s'):
            gaps.append(make_gap(cluster,floors,350 if kind=='s' else 190))
        else:
            add_cluster_pieces(cluster,floors)
        clusters.append(cluster)
    shoulder = []
    for route in routes:
        for i in range(2,len(route['tiles'])-2):
            if not safe_center(route,i,100):
                continue
            # Suppress incidental rubble near a major cluster, its gap run-up or
            # recovery. Remaining authored spacing is 5 m, alternating shoulders.
            if any(c['route']==route['id'] and abs(i-c['tile_index'])*500 <
                   (1400 if 'gap' in c['kind'] else 600) for c in clusters):
                continue
            c,f = route['nodes'][i],direction(route['tiles'],i)
            t = 165 if route['carrier_return'] else (165 if i%2 else -165)
            pos = frame(c,f,0,t)
            z = floors.at(route['source_floor'],pos[0],pos[1])
            size = [130+(i%3)*15,90,25+(i%3)*7]
            piece = primitive(f'ML_{route["id"]}_shoulder{i}',c,f,0,t,size,z)
            piece.update({'route':route['id'],'path':route['path'],'segment':route['segment'],
                          'carrier_return':route['carrier_return'],'across':t})
            shoulder.append(piece)
    result = {'schema_version':1,'units':'cm','source':SOURCE,'source_sha256':SOURCE_SHA256,
              'source_floor_indices':[318,319,320,321],'source_room_floor':322,
              'coordinate_contract':'Source actor locations already include X-175; vertices local; do not shift twice.',
              'status':'finite authored candidates; native collision and owning-input certification pending',
              'routes':routes,'rooms':rooms,'clusters':clusters,'shoulder_rubble':shoulder,'gaps':gaps,
              'return_route':{'legs':['orange_3 reverse','yellow_2 reverse','yellow_1 reverse'],
                  'nodes':return_nodes(routes),'min_lane_width':160,'max_new_step':0,
                  'required_jump_climb_sprint':False,
                  'last_section':'Existing fork/mouth/mining-door connector; verify preserved floor south of source clip Y3200.',
                  'native_verified':False},
              'avoidance':{'room_obstacles':False,'mouth_clearance':1000,'bend_crossing_junction_clearance':500,
                           'extra_rooms_tubes_roofs':False,'same_path_recovery':True},
              'physical_devices_tested':False,'native_verified':False}
    result['offline_checks'] = validate(result,floors)
    return result


def validate(result,floors):
    """Reject data-contract errors; this is explicitly not native movement proof."""
    assert len(result['routes'])==12 and len(result['clusters'])>=30
    assert len({c['id'] for c in result['clusters']})==len(result['clusters'])
    counts = Counter(c['route'] for c in result['clusters'])
    assert len(counts)==12 and min(counts.values())>=1
    density = Counter(p['route'] for p in result['shoulder_rubble'])
    for cluster in result['clusters']:
        assert len(cluster['decisions'])>=3
        if cluster['carrier_return']:
            assert 'gap' not in cluster['kind']
            assert cluster['return_safe_lane']['width']>=120
            # The blockers are all to the right of the continuous left lane.
            for piece in cluster['primitives']:
                if piece['collision']:
                    assert piece['across']-piece['size'][1]/2 >= 60
        for room in result['rooms']:
            assert not overlap(cluster['footprint'],room['bounds']), ('Room blocked',cluster['id'],room['name'])
    for i,cluster in enumerate(result['clusters']):
        for other in result['clusters'][i+1:]:
            if cluster['route']==other['route']:
                assert not overlap(cluster['footprint'],other['footprint']), ('Major envelopes overlap',cluster['id'],other['id'])
    cross_layer_samples = 0
    for gap in result['gaps']:
        assert gap['depth_cm']>=250 and gap['depth_cm']<=350
        assert gap['recovery']['rise']<=40 and gap['recovery']['clear_width']>=120
        assert gap['floor_grade_degrees']<=5 and not gap['lethal']
        for a in (-gap['length']/2,0,gap['length']/2,gap['length']/2+540):
            for t in (-200,0,150):
                point = frame(gap['center'],gap['forward'],a,t)
                for index in range(318,322):
                    if index==gap['source_floor']:
                        continue
                    z = floors.at(index,point[0],point[1],False)
                    assert z is None or z<gap['pit_floor']-100 or z>gap['center'][2]+250, ('Recovery overlaps another layer',gap['id'],index,point,z)
                    cross_layer_samples += 1
    # JSON serialization also forbids non-finite accidentally generated coordinates.
    json.dumps(result,allow_nan=False)
    return {'passed':True,'scope':'offline source/data/envelope checks only; no native collision or play claim',
            'source_hash_passed':True,'routes':12,'major_clusters':len(result['clusters']),
            'major_clusters_by_route':dict(sorted(counts.items())),
            'shoulder_rubble':len(result['shoulder_rubble']),
            'shoulder_rubble_by_route':dict(sorted(density.items())),
            'recoverable_gaps':len(result['gaps']),'cross_layer_floor_samples':cross_layer_samples,
            'return_lane_width':160,'native_verified':False}


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
    print(json.dumps(plan(root)['offline_checks'],indent=2))
