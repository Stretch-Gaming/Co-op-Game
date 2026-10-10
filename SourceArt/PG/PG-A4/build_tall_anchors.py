"""PG-A4 zipline anchors, rebuilt taller for PG-7 (#29). Original Blender Python modeling.
Opens the PG-A4 source .blend, replaces the two anchor meshes, bakes their 1K base color
and packed mask (red AO, green roughness, blue metallic), exports FBX and saves the .blend:

    blender -b SourceArt/PG/PG-A4/PG-A4_ZiplineParts.blend --python SourceArt/PG/PG-A4/build_tall_anchors.py -- <output folder>

The helpers below are unchanged from the PG-A4 candidate generator. Model units are metres.
"""
import bpy, bmesh, math, json, random
import numpy as np
from pathlib import Path
from mathutils import Vector

def lin(hexcode):
    c=[int(hexcode[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in c)

# Desaturated timber and flax do not claim the amber/gold/jade gameplay colors.
PALETTE={
 'wood':('#493D40','#938078',.84,0),
 'wood_edge':('#665550','#B09A88',.79,0),
 'iron':('#38404F','#7A6E68',.58,.72),
 'iron_edge':('#4A4652','#A4A5AD',.50,.80),
 'rope':('#625B60','#BBB3A0',.91,0),
 'rope_edge':('#77707A','#CDC3B3',.88,0),
 'rock':('#4A4652','#7A6E68',.95,0),
 'rock_edge':('#5C5664','#95857A',.92,0),
}
sources={}
def source_mat(kind, cable=False):
    key=kind+('_tile' if cable else '')
    if key in sources:return sources[key]
    lo,hi,rough,metal=PALETTE[kind]
    m=bpy.data.materials.new('SRC_'+key); m.use_nodes=True
    n=m.node_tree.nodes; n.clear(); l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial'); emit=n.new('ShaderNodeEmission')
    l.new(emit.outputs[0],out.inputs['Surface'])
    tex=n.new('ShaderNodeTexCoord'); sep=n.new('ShaderNodeSeparateXYZ')
    l.new(tex.outputs['UV' if cable else 'Generated'],sep.inputs[0])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=0
    ramp.color_ramp.elements[0].color=(*lin(lo),1)
    ramp.color_ramp.elements[1].position=1
    ramp.color_ramp.elements[1].color=(*lin(hi),1)
    if cable:
        # Circumferential painted highlight, never a non-tiling length gradient.
        mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=6*math.pi
        l.new(sep.outputs['Y'],mult.inputs[0])
        sine=n.new('ShaderNodeMath');sine.operation='SINE';l.new(mult.outputs[0],sine.inputs[0])
        mad=n.new('ShaderNodeMath');mad.operation='MULTIPLY_ADD';mad.inputs[1].default_value=.35;mad.inputs[2].default_value=.6
        l.new(sine.outputs[0],mad.inputs[0]);l.new(mad.outputs[0],ramp.inputs[0])
    else:l.new(sep.outputs['Z'],ramp.inputs[0])
    if 'wood' in kind:
        # Three broad painted grain bands, not scanned grain or high frequency noise.
        wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Z'
        wave.inputs['Scale'].default_value=2.1;wave.inputs['Distortion'].default_value=.6
        l.new(tex.outputs['Generated'],wave.inputs['Vector'])
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.16
        l.new(ramp.outputs[0],mix.inputs[1]);l.new(wave.outputs['Color'],mix.inputs[2])
        l.new(mix.outputs[0],emit.inputs['Color'])
    else:l.new(ramp.outputs[0],emit.inputs['Color'])
    m['roughness']=rough;m['metallic']=metal;m['kind']=kind
    sources[key]=m;return m

parts=[]
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def register(o,name,kind,smooth=False):
    o.name=name;o.data.materials.append(source_mat(kind))
    for p in o.data.polygons:p.use_smooth=smooth
    parts.append(o);return o
def bevel(o,width,kind):
    o.data.materials.append(source_mat(kind+'_edge' if kind+'_edge' in PALETTE else kind))
    mod=o.modifiers.new('Wide worn bevel','BEVEL');mod.width=width;mod.segments=1;mod.material=1
    active(o);bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
def box(name,center,size,kind='iron',edge=.015,rot=None,uneven=False):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object
    o.dimensions=size;active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    register(o,name,kind)
    bevel(o,edge,kind)
    if uneven:
        # Coarse 2 mm edge drift, exact mounting faces kept unchanged.
        for v in o.data.vertices:
            v.co.y+=.002*math.sin(v.co.z*9+v.co.x*14)
            v.co.x+=.002*math.sin(v.co.z*11+v.co.y*8)
    if rot:o.rotation_euler=rot
    return o
def beam(name,a,b,width,depth,kind='wood',edge=.02,uneven=True):
    a,b=Vector(a),Vector(b)
    if kind=='wood' and uneven:
        # Long timbers bow gently between exact end mount centres. Six stations
        # make actual broad silhouette variation, rather than surface noise.
        length=(b-a).length;c=min(edge,width*.24,depth*.24)
        profile=[(-width/2+c,-depth/2),(width/2-c,-depth/2),(width/2,-depth/2+c),(width/2,depth/2-c),
                 (width/2-c,depth/2),(-width/2+c,depth/2),(-width/2,depth/2-c),(-width/2,-depth/2+c)]
        ts=[0,.025,.33,.66,.975,1];vs=[];fs=[]
        for t in ts:
            taper=.93 if t in (0,1) else 1+.025*math.sin(t*5)
            bow=math.sin(math.pi*t)*min(.013,length*.018)
            for x,y in profile:vs.append((x*taper+bow,y*taper-bow*.55,length*(t-.5)))
        for i in range(5):
            for j in range(8):fs.append((i*8+j,i*8+(j+1)%8,(i+1)*8+(j+1)%8,(i+1)*8+j))
        fs+=[tuple(range(7,-1,-1)),tuple(range(40,48))]
        me=bpy.data.meshes.new('Bent chamfered timber');me.from_pydata(vs,[],fs);me.update()
        o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.location=(a+b)*.5;register(o,name,kind)
        me.materials.append(source_mat('wood_edge'))
        for i,p in enumerate(me.polygons):
            if i<40 and (i%8%2==1 or i//8 in (0,4)):p.material_index=1
    else:o=box(name,(a+b)*.5,(width,depth,(b-a).length),kind,edge,uneven=uneven)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def cylinder(name,center,radius,depth,kind='iron',axis='Y',vertices=10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=center)
    o=bpy.context.object;register(o,name,kind)
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    elif axis=='X':o.rotation_euler[1]=math.pi/2
    return o
def ring(name,center,major,minor,kind='rope',axis='Z',n=12,k=4):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=n,minor_segments=k,location=center)
    o=bpy.context.object;register(o,name,kind,True)
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    elif axis=='X':o.rotation_euler[1]=math.pi/2
    return o
def bolt(name,center,axis='Y',radius=.025):return cylinder(name,center,radius,.014,'iron_edge',axis,6)


assets={};metrics={}
def finish(name,builder,custom_uv=False):
    global parts
    parts=[];builder();bpy.ops.object.select_all(action='DESELECT')
    for p in parts:p.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join();o=bpy.context.object;o.name=name
    scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if not custom_uv:
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
        bm.to_mesh(o.data);bm.free();o.data.update()
    if not custom_uv:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(68),island_margin=.014,area_weight=.5)
        bpy.ops.object.mode_set(mode='OBJECT')
    # Recalculate outward normals on manufactured closed solids.
    if not custom_uv:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
    o.data.calc_loop_triangles()
    metrics[name]={'triangles':len(o.data.loop_triangles),'dimensions_cm':[round(d*100,2) for d in o.dimensions],
      'bounds_cm':[[round(min((o.matrix_world@v.co)[a] for v in o.data.vertices)*100,2),round(max((o.matrix_world@v.co)[a] for v in o.data.vertices)*100,2)] for a in range(3)],
      'pivot_cm':[0,0,0],'uv':'length U 0..1, circumferential V in three strips; repeat U' if custom_uv else 'unique packed UV atlas',
      'material_slots_after_bake':1}
    if 'Trolley' in name:assert metrics[name]['triangles']<2000,(name,metrics[name])
    if 'Anchor' in name:assert metrics[name]['triangles']<=5000
    assets[name]=o;print('MODEL',name,metrics[name],flush=True);return o


def image_new(name,colorspace):
    im=bpy.data.images.new(name,width=1024,height=1024,alpha=False)
    im.colorspace_settings.name=colorspace;return im

def target(mat,im):
    n=mat.node_tree.nodes
    for node in n:node.select=False
    node=n.new('ShaderNodeTexImage');node.image=im;node.select=True;n.active=node
    return node

def write_png(im,path):
    im.filepath_raw=str(path);im.file_format='PNG';im.save()

def bake_asset(name,o):
    print('BAKE START',name,flush=True)
    for other in assets.values():other.hide_render=True
    o.hide_render=False;active(o)
    mats=list(o.data.materials)
    color=image_new('T_'+name[3:]+'_BaseColor','sRGB')
    temp_nodes=[target(m,color) for m in mats]
    bpy.ops.object.bake(type='EMIT')
    write_png(color,ROOT/'textures'/f'{color.name}.png')
    for m,n in zip(mats,temp_nodes):m.node_tree.nodes.remove(n)
    ao=image_new(name+'_AO_temp','Non-Color')
    temp_nodes=[target(m,ao) for m in mats]
    neighbors=[]
    if name=='SM_ZiplineCable':
        for dx in (-1,1):
            cp=o.copy();cp.data=o.data.copy();scene.collection.objects.link(cp);cp.location.x=dx;cp.hide_render=False;neighbors.append(cp)
    bpy.ops.object.bake(type='AO')
    for cp in neighbors:bpy.data.objects.remove(cp,do_unlink=True)
    for m,n in zip(mats,temp_nodes):m.node_tree.nodes.remove(n)
    rm=image_new(name+'_RM_temp','Non-Color')
    temp_nodes=[target(m,rm) for m in mats]
    original_links=[]
    for m in mats:
        n=m.node_tree.nodes;l=m.node_tree.links;em=next(v for v in n if v.type=='EMISSION')
        socket=em.inputs['Color'];original_links.append((m,socket.links[0].from_socket))
        for link in list(socket.links):l.remove(link)
        socket.default_value=(1,m['roughness'],m['metallic'],1)
    bpy.ops.object.bake(type='EMIT')
    for m,from_socket in original_links:
        em=next(v for v in m.node_tree.nodes if v.type=='EMISSION');m.node_tree.links.new(from_socket,em.inputs['Color'])
    for m,n in zip(mats,temp_nodes):m.node_tree.nodes.remove(n)
    a=np.empty(1024*1024*4,dtype=np.float32);r=np.empty_like(a)
    ao.pixels.foreach_get(a);rm.pixels.foreach_get(r);a=a.reshape((1024,1024,4));r=r.reshape((1024,1024,4))
    r[:,:,0]=np.maximum(.32,a[:,:,0]);r[:,:,3]=1
    if name=='SM_ZiplineCable':
        # Enforce exactly equal border texels for texture-repeat seams.
        edge=(r[:,0,:]+r[:,-1,:])*.5;r[:,0,:]=edge;r[:,-1,:]=edge
        c=np.empty(1024*1024*4,dtype=np.float32);color.pixels.foreach_get(c);c=c.reshape((1024,1024,4))
        edge=(c[:,0,:]+c[:,-1,:])*.5;c[:,0,:]=edge;c[:,-1,:]=edge;color.pixels.foreach_set(c.ravel());color.update()
        write_png(color,ROOT/'textures'/f'{color.name}.png')
    packed=image_new('T_'+name[3:]+'_ORM','Non-Color');packed.pixels.foreach_set(r.ravel());packed.update()
    write_png(packed,ROOT/'textures'/f'{packed.name}.png')
    bpy.data.images.remove(ao);bpy.data.images.remove(rm)
    m=bpy.data.materials.new('M_'+name[3:]+'_BakedPreview');m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
    col=n.new('ShaderNodeTexImage');col.image=color;col.label='sRGB base color'
    orm=n.new('ShaderNodeTexImage');orm.image=packed;orm.label='Linear R AO / G Roughness / B Metallic'
    sep=n.new('ShaderNodeSeparateColor');l.new(orm.outputs['Color'],sep.inputs[0])
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35
    l.new(col.outputs['Color'],mix.inputs[1]);l.new(sep.outputs['Red'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    l.new(sep.outputs['Green'],bs.inputs['Roughness']);l.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    o.data.materials.clear();o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=0
    # Bake source materials remain in the .blend for inspection/regeneration.
    for sm in mats:sm.use_fake_user=True
    tri=o.modifiers.new('Export triangulation','TRIANGULATE');active(o);bpy.ops.object.modifier_apply(modifier=tri.name)
    if name=='SM_ZiplineCable':
        # Match vertex normals on the repeated end rings as well as geometry.
        o.data.update();normals=[v.normal.copy() for v in o.data.vertices]
        for s in range(3):
            for j in range(8):
                a=s*328+j;b=s*328+320+j;n=(normals[a]+normals[b]).normalized()
                normals[a]=n;normals[b]=n
        o.data.normals_split_custom_set_from_vertices(normals)
    bpy.ops.export_scene.fbx(filepath=str(ROOT/'exports'/f'{name}.fbx'),use_selection=True,object_types={'MESH'},
        global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Y',axis_up='Z',
        use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,
        add_leaf_bones=False,bake_anim=False)
    color.pack();packed.pack()
    print('BAKE & EXPORT DONE',name,flush=True)


# ---------------------------------------------------------------------------
# Tall anchors (PG-7 follow-up). Both anchors are now matching timber gantries,
# so a hanging rider (feet 245 cm under the cable) clears the floor at both ends.
TOP_EYE_HEIGHT=2.80     # boarding ledge to cable
BOTTOM_EYE_HEIGHT=2.30  # landing floor to cable

def gantry(G,sx,eye_name,footings=True):
    """Eye at the origin. Posts stand at x=sx*0.20, behind the eye along the cable."""
    X=lambda x:sx*x
    base=G if footings else G+.18
    for s in (-1,1):
        beam('Worn timber post',(X(.20),s*.50,base+.12),(X(.20),s*.48,.30),.20,.21,'wood',.042)
        box('Foot shoe',(X(.20),s*.50,base+.18),(.27,.28,.16),'iron',.024)
        beam('Splayed rear brace',(X(.95),s*.56,base+.13),(X(.20),s*.49,-.62),.14,.15,'wood',.032)
        if footings:box('Stone footing',(X(.55),s*.52,G+.07),(1.02,.44,.14),'rock',.035,uneven=True)
        for z in (-.52,-.555,-.59):ring('Post rope collar',(X(.20),s*.49,z),.146,.013,'rope','Z',12,4)
        for z in (base+.55,-.43,.17):bolt('Post rivet',(X(.084),s*.49,z),'X',.033)
        beam('Knee brace',(X(.20),s*.48,-.39),(X(.20),s*.15,.14),.11,.13,'wood',.026)
        for y in (.30,.33):ring('Mid tie lashing',(X(.20),s*y,base+1.05),.11,.012,'rope','Y',10,4)
    # Mid tie: the taller posts get a crooked cross timber at knee height.
    beam('Mid tie timber',(X(.20),-.66,base+1.03),(X(.20),.66,base+1.08),.15,.16,'wood',.034)
    beam('Crooked cross timber',(X(.20),-.69,.24),(X(.20),.69,.27),.21,.24,'wood',.045)
    box('Eye backing',(X(.063),0,.08),(.085,.32,.36),'iron',.025)
    ring(eye_name,(0,0,0),.079,.026,'iron','X',16,6)
    for y in (-.11,.11):bolt('Eye backing bolt',(X(.012),y,.17),'X',.028)
    for y in (-.10,-.06,.06,.10):ring('Crossbar lashing',(X(.20),y,.25),.157,.012,'rope','Y',12,4)

def top_anchor_tall():
    gantry(-TOP_EYE_HEIGHT,-1,'Launch eye')

def bottom_anchor_tall():
    G=-BOTTOM_EYE_HEIGHT
    gantry(G,1,'Landing eye',footings=False)
    # The landing keeps its strapped timber skid and chipped rock, now as the gantry's sill and ballast.
    box('Timber skid',(.52,0,G+.09),(1.30,1.45,.18),'wood',.04,uneven=True)
    for y in (-.36,.36):
        box('Skid band',(.52,y,G+.185),(1.0,.055,.028),'iron',.008)
        for x in (.12,.90):bolt('Skid rivet',(x,y,G+.207),'Z',.021)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(.66,0,G+.55));o=bpy.context.object
    for v in o.data.vertices:v.co*=1+.065*math.sin(v.index*3.73)
    o.scale=(.40,.38,.40);active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    register(o,'Chipped rock ballast','rock')
    # Flax backstay from the eye backing down to the ballast rock.
    beam('Flax backstay',(.11,0,-.02),(.62,0,G+.82),.045,.045,'rope',.012,False)
    for t in (.3,.6):
        p=Vector((.11,0,-.02)).lerp(Vector((.62,0,G+.82)),t)
        ring('Backstay whipping',tuple(p),.04,.010,'iron','Z',8,4)

import sys as _sys
OUT=Path(_sys.argv[_sys.argv.index('--')+1])
ROOT=OUT
for folder in ('exports','textures'):(OUT/folder).mkdir(parents=True,exist_ok=True)
random.seed(38)
scene=bpy.context.scene
# Reuse the source materials saved in the .blend instead of making .001 copies.
for m in bpy.data.materials:
    if m.name.startswith('SRC_'):sources[m.name[4:]]=m
for name in ('SM_ZiplineAnchor_Top','SM_ZiplineAnchor_Bottom'):
    o=bpy.data.objects.get(name)
    if o:bpy.data.objects.remove(o,do_unlink=True)
    c=bpy.data.collections.get(name)
    if c:bpy.data.collections.remove(c)
    for suffix in ('BaseColor','ORM'):
        im=bpy.data.images.get('T_'+name[3:]+'_'+suffix)
        if im:bpy.data.images.remove(im)
    m=bpy.data.materials.get('M_'+name[3:]+'_BakedPreview')
    if m:bpy.data.materials.remove(m)
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name.startswith('SM_'):o.hide_render=True;o.hide_set(False)
for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.bake.margin=12;scene.render.bake.use_clear=True
bpy.ops.object.select_all(action='DESELECT')
finish('SM_ZiplineAnchor_Top',top_anchor_tall)
finish('SM_ZiplineAnchor_Bottom',bottom_anchor_tall)
for name,o in assets.items():bake_asset(name,o)
json.dump(metrics,open(OUT/'metrics.json','w'),indent=2)
for name,o in assets.items():
    o.rotation_mode='XYZ';o.rotation_euler=(0,0,0)
    col=bpy.data.collections.new(name);scene.collection.children.link(col)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o)
    o['PG_A4_pivot']='Cable centreline at origin; X travel; Z up'
    o['dimensions_cm']=metrics[name]['dimensions_cm'];o['triangles']=metrics[name]['triangles']
for c in bpy.data.collections:
    if c.name.startswith('SM_'):c.hide_render=True;c.hide_viewport=c.name!='SM_ZiplineTrolley_A'
scene['PG_A4_notes']='Original Blender Python models. Five assets overlap at exact functional origins; enable one collection at a time. Textures packed. Anchors rebuilt taller for PG-7: top eye 2.80 m, bottom eye 2.30 m above the floor.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'PG-A4_ZiplineParts.blend'))
print('ALL COMPLETE',json.dumps(metrics),flush=True)
