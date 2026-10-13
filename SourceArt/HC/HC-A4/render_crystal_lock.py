"""Source-only cave/15 m previews in the current dedicated HC_A4_ scene.
Original lighting/render code, CC0 1.0 Universal. Run after native FBX validation.
"""
import math
from pathlib import Path

import bpy
from mathutils import Vector


def setup(mod, repo, output):
    scene=bpy.context.scene
    if not scene.name.startswith('HC_A4_'):raise RuntimeError('Preview only in HC_A4_ scene')
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    kit=mod.kit_at(repo)
    visual=next(o for o in scene.objects if o.type=='MESH' and not o.name.startswith('UCX_'))
    for o in scene.objects:
        if o.name.startswith('UCX_'):o.hide_render=True;o.hide_set(True)
    try:scene.render.engine='BLENDER_EEVEE'
    except TypeError as exc:raise RuntimeError(str(exc))
    scene.view_settings.view_transform='AgX'
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    world=bpy.data.worlds.new('HC_A4_CavePreview');world.use_nodes=True
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs['Color'].default_value=kit.hex_rgba('#1E2433')
    bg.inputs['Strength'].default_value=.32;scene.world=world
    floor=kit.chunky_block('PreviewFloor',size=(38,38,.12),bevel=0,wobble=0,material=mod.material('M_HC_A4_PreviewFloor','#4A4652',.95,kit))
    floor.location=(0,0,-.06)
    lights=[]
    for name,col,power,loc,size in [('HC_A4_WarmKey','#FFCF92',90,(-2,-3,3),3),('HC_A4_ColdFill','#A9D3D7',32,(3,1,2),3),('HC_A4_Rim','#8E9FB7',50,(-2,3,2.5),2)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=kit.hex_rgba(col)[:3];d.shape='DISK';d.size=size
        o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
        o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
    data=bpy.data.cameras.new('HC_A4_PreviewCamera');camera=bpy.data.objects.new('HC_A4_PreviewCamera',data);scene.collection.objects.link(camera);scene.camera=camera
    return scene,visual,camera,kit,out


def render_state(scene,visual,camera,kit,out,mod,lit,distant=False):
    gem=visual.data.materials[1]
    mod.set_lit(gem,lit,kit)
    if distant:
        scene.render.resolution_x=1280;scene.render.resolution_y=720
        camera.data.lens=18;camera.data.sensor_width=36;camera.data.sensor_fit='HORIZONTAL'
        camera.location=(0,-15,.65);target=Vector((0,0,.5))
        filename='15m_'+('lit' if lit else 'unlit')+'.png'
    else:
        scene.render.resolution_x=640;scene.render.resolution_y=640
        camera.data.lens=50;camera.data.sensor_width=36;camera.data.sensor_fit='HORIZONTAL'
        camera.location=(1.65,-2.35,1.65);target=Vector((0,0,.46))
        filename='cave_'+('lit' if lit else 'unlit')+'.png'
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/filename)
    bpy.ops.render.render(write_still=True)
    print({'render':filename,'state':'lit' if lit else 'unlit','distance_m':(camera.location-target).length,'size':[scene.render.resolution_x,scene.render.resolution_y],'source_only':True})


def main(mod,repo,output):
    scene,visual,camera,kit,out=setup(mod,repo,output)
    for distant in (False,True):
        for lit in (False,True):render_state(scene,visual,camera,kit,out,mod,lit,distant)
    # The scale sheet uses the existing pipeline's four-angle rig in this disposable scene.
    for o in list(scene.objects):
        if o.type!='MESH' or o.name=='PreviewFloor':bpy.data.objects.remove(o,do_unlink=True)
    mod.set_lit(visual.data.materials[1],True,kit)
    kit.preview_sheet([visual],str(out/'scale_and_angles.png'),title='SM_CrystalLock',resolution=384,with_figure=True)
    mod.set_lit(visual.data.materials[1],False,kit)
    print('Source previews complete; original emission restored to off')
