"""Pure geometry transformations. Source capture is never overwritten."""
import gzip, json
from pathlib import Path
BASE='/Game/Hazards/Art/SixRoundConnection'
SHIFT=-175
# Replacement of the shared raised hall by isolated, vertically separated solo connectors.
CUTS=[([-3750,14250,-1500],[3750,16750,5000]),([1950,22950,610],[2600,23550,1150]),([1250,24450,610],[1750,25300,1000]),([-825,23820,610],[1800,24420,1000]),([1200,23820,610],[1800,25300,1000])]
GAPS=[{'ColorSlot':0,'stage':'first','center':[5000,7500],'length':200},{'ColorSlot':1,'stage':'first','center':[-5000,7500],'length':200},{'ColorSlot':2,'stage':'first','center':[8000,5000],'length':200},{'ColorSlot':3,'stage':'first','center':[-9000,5000],'length':200},{'ColorSlot':0,'stage':'second','center':[500,18000],'length':350},{'ColorSlot':1,'stage':'second','center':[1500,22000],'length':350},{'ColorSlot':2,'stage':'second','center':[6000,21000],'length':350},{'ColorSlot':3,'stage':'second','center':[-6000,18000],'length':350}]
def subtract_box(record,lo,hi):
    # Split each triangle against six planes; retain the exterior pieces. Attributes
    # interpolate at cuts so the preserved painted appearance stays continuous.
    original=list(record['triangles']);new=[]
    fields=['vertices','normals','uvs','vertex_colors']
    def split(poly,axis,value,greater):
        yes=[];no=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            av=a[0][axis]-value;bv=b[0][axis]-value
            ai=av>=0 if greater else av<=0;bi=bv>=0 if greater else bv<=0
            (yes if ai else no).append(a)
            if ai!=bi:
                t=av/(av-bv)
                point=[[x+(y-x)*t for x,y in zip(aa,bb)] for aa,bb in zip(a,b)]
                yes.append(point);no.append(point)
        return yes,no
    def append(poly):
        if len(poly)<3:return
        indices=[]
        for v in poly:
            indices.append(len(record['vertices']))
            for field,data in zip(fields,v):record[field].append(data)
        for j in range(1,len(indices)-1):new.extend([indices[0],indices[j],indices[j+1]])
    for n in range(0,len(original),3):
        tri=original[n:n+3]
        if not all(min(record['vertices'][k][i] for k in tri)<=hi[i] and max(record['vertices'][k][i] for k in tri)>=lo[i] for i in range(3)):
            new.extend(tri);continue
        remaining=[[list(record[field][k]) for field in fields] for k in tri]
        for axis in range(3):
            for value,greater in [(lo[axis],True),(hi[axis],False)]:
                if not remaining:break
                remaining,outside=split(remaining,axis,value,greater);append(outside)
    record['triangles']=new
def inside_cut(v):return any(all(lo[i]<=v[i]<=hi[i] for i in range(3)) for lo,hi in CUTS)
def overlaps_cut(vertices):
    return any(all(min(v[i] for v in vertices)<=hi[i] and max(v[i] for v in vertices)>=lo[i] for i in range(3)) for lo,hi in CUTS)
def source_scene(root):
    """Normalize delivered PR124 connection back to local pre-shift coordinates.

    Source records already have world X-175 applied to their actor/instance
    locations. Normalize only those locations so the unchanged placement
    transform applies exactly one shift. Procedural vertices are already local.
    Sparse source_index IDs stay stable across the new mesh namespace.
    """
    data=json.loads(gzip.decompress((root/'SourceArt/HC/EnvironmentConnection/connection.json.gz').read_bytes()))
    meta=data['metadata']
    assert meta['reference_pr']==90 and meta['maze_offset_x']==SHIFT and meta['cut_world_y']==3200
    assert 909 in meta['excluded_non_environment_volumes']
    records=[{'kind':'excluded','name':'Excluded_'+str(i),'source_index':i} for i in range(916)]
    for r in data['components']:
        index=r['source_index'];assert index!=909
        # Prototype-wide safety backstop is not a recoverable pit and would
        # catch carrier/chasm falls above the new20m chasm death plane.
        if index in (908,701,702,703):continue
        if index in (697,698,699,700,887,888,889,890):r['collision']=False # Old partner-dependent blocks are replaced by declared solo platforms; door frames remain dressing.
        r['location'][0]-=SHIFT
        for instance in r.get('instances',[]):instance['location'][0]-=SHIFT
        records[index]=r
    return {'components':records,'metadata':meta,'source_records':len(data['components']),'maze_detail_reference':'PR #90 via PR124 connection, local-X normalization before one placement translation'}

def scene(root):
    data=source_scene(root)
    for gap in GAPS:
        record=data['components'][318+gap['ColorSlot']]
        x,y=gap['center'];z=floor_z(record,x,y,0)
        subtract_box(record,[x-260,y-gap['length']/2,z-300],[x+260,y+gap['length']/2,z+300])
    for r in data['components'][316:]:
        if r['kind']=='procedural':
            assert r['rotation']==[0,0,0] and r['scale']==[1,1,1]
            for cut_index,(lo,hi) in enumerate(CUTS):
                if cut_index>0 and r['source_index'] in (318,319,320,321,322):continue # Door cuts never remove navigation floor surfaces.
                # Native contacts prove the two wall/trim meshes retain a10cm
                # collar at610 intersecting the capsule's lower spherical cap.
                # Remove only those collars; unchanged scenery/floors stay intact.
                if cut_index>=3 and r['source_index'] in (324,884):lo=[lo[0],lo[1],580]
                subtract_box(r,[lo[i]-r['location'][i] for i in range(3)],[hi[i]-r['location'][i] for i in range(3)])
    return data
def floor_z(record,x,y,fallback):
    # Exact barycentric sample of captured path floor triangles, independent of Unreal.
    best=None;verts=record['vertices']; tris=record['triangles']
    for n in range(0,len(tris),3):
        a,b,c=[verts[k] for k in tris[n:n+3]]
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8:continue
        u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        if u>=-1e-5 and v>=-1e-5 and u+v<=1.00001:
            z=u*a[2]+v*b[2]+(1-u-v)*c[2]
            if best is None or z>best:best=z
    return fallback if best is None else round(best,3)

def floor_surface(record,x,y):
    """Captured top surface and normal; no native-obstruction result is trusted as design data."""
    best=None;vertices=record['vertices'];triangles=record['triangles']
    for n in range(0,len(triangles),3):
        a,b,c=[vertices[k] for k in triangles[n:n+3]]
        denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator)<1e-8:continue
        u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denominator
        v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denominator
        if u<-.00001 or v<-.00001 or u+v>1.00001:continue
        z=u*a[2]+v*b[2]+(1-u-v)*c[2]
        if best and best[0]>=z:continue
        ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
        normal=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
        length=sum(p*p for p in normal)**.5
        if not length:continue
        sign=1 if normal[2]>0 else -1
        best=(z,[sign*p/length for p in normal])
    return best
