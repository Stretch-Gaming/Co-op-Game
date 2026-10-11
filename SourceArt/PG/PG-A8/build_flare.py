"""Original PG-A8 geometry/audio. Run in factory-startup headless Blender; see README."""
import argparse
import json
import math
import sys
import wave
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

PROMPT = ('A hand flare matching a 6 x 6 x 22 cm greybox, broad faceted metal heel, '
          'wrapped grip, ivory paper canister, chunky amber burning tip; '
          'stylized hand-painted game asset, chunky exaggerated proportions, slightly '
          'uneven shapes, soft wide bevels, simple painted color, gradient from dark '
          'base to lighter top, no fine surface noise, no photo textures')


def material(name, color, roughness, metallic=0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def lathe(name, rings, mat, sides=12, uneven=0):
    # Rings: (z cm, radius cm, x offset cm); independent capped manifold shells.
    vertices = []
    for z, r, x in rings:
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            radius = r * (1 + uneven * math.sin(3 * angle + .5))
            vertices.append(((x + radius * math.cos(angle)) / 100,
                             radius * math.sin(angle) / 100, z / 100))
    faces = [tuple(reversed(range(sides)))]
    for row in range(len(rings) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((row*sides+i, row*sides+j, (row+1)*sides+j, (row+1)*sides+i))
    faces.append(tuple((len(rings)-1)*sides+i for i in range(sides)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh(candidate):
    mats = [material('M_FlareGrip', (.22,.15,.085), .85),
            material('M_FlareBody', (.68,.49,.27), .8),
            material('M_FlareMetal', (.13,.16,.23), .48, .45),
            # linear RGB corresponding to torch amber #FFB347
            material('M_FlareAmber', (1,.4508,.063), .65, emission=1.2)]
    parts = [lathe('Heel', [(0,2.6,0),(.4,3,0),(1.1,3,0),(1.5,2.4,0)], mats[2]),
             lathe('Grip', [(1.1,2.1,0),(1.5,2.4,0),(7.6,2.25,.1),(8.1,2.1,0)], mats[0], uneven=.02),
             lathe('Canister', [(7.7,2.2,0),(8.2,2.55,0),(14.6,2.5,.1),(15.1,2.1,0)], mats[1], uneven=.025),
             lathe('Lip', [(14.7,2.4,0),(15,2.85,0),(15.7,2.85,0),(16,2.3,0)], mats[2]),
             lathe('Ember', [(15.7,2.1,0),(16.4,2.25,0),(17,1.9,.1)], mats[3], uneven=.04)]
    if candidate == 'A':
        # Two broad cloth bands stay readable without fine rope/thread geometry.
        for z, x in [(3.2,-.04),(6.2,.06)]:
            parts.append(lathe('Wrap', [(z,2.35,x),(z+.2,2.6,x),(z+.8,2.55,x),(z+1,2.3,x)], mats[1], uneven=.025))
        flame = [(16.5,1.6,0),(17.5,2.25,.1),(19,1.75,.4),(20.3,1.2,.9),(21.4,.55,.65),(22,.12,.9)]
    else:
        parts.append(lathe('Collar', [(6,2.4,0),(6.3,2.8,0),(7.7,2.8,0),(8,2.4,0)], mats[2]))
        flame = [(16.5,1.4,0),(18,1.8,0),(20,.8,0),(22,.08,0)]
    parts.append(lathe('Flame', flame, mats[3], sides=10, uneven=.04))
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts: part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = 'SM_HandFlare'
    # Stable four slots; joining retains material-index assignments.
    assert [m.name for m in obj.data.materials] == ['M_FlareMetal','M_FlareGrip','M_FlareBody','M_FlareAmber']
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj['brief'] = PROMPT
    obj['candidate'] = candidate
    obj['license'] = 'Original PK work, CC0 1.0 Universal; public redistribution allowed; no attribution required.'
    return obj


def camera_at(position, target):
    bpy.ops.object.camera_add(location=position)
    c = bpy.context.object
    c.rotation_euler = (Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
    c.data.type = 'ORTHO'
    c.data.ortho_scale = .3
    bpy.context.scene.camera = c
    return c


def render(obj, path, cave=False):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.035,.05,.095,1) if cave else (.10,.13,.20,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .25 if cave else .65
    scene.view_settings.view_transform = 'AgX'
    c = camera_at((.33,-.52,.33), (0,0,.11))
    lights = []
    for pos, energy, color in [((-.2,-.3,.5),.22 if cave else 1.2,(1,.72,.40)),((.3,.1,.3),.1 if cave else .6,(.30,.60,1))]:
        bpy.ops.object.light_add(type='AREA', location=pos)
        light = bpy.context.object
        light.data.energy = energy
        light.data.color = color
        light.data.shape = 'DISK'
        light.data.size = .3
        light.rotation_euler = (Vector((0,0,.11))-light.location).to_track_quat('-Z','Y').to_euler()
        lights.append(light)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    for helper in [c]+lights: bpy.data.objects.remove(helper, do_unlink=True)


def audio(output):
    # Periodic filtered noise: FFT bins define a cyclic band-limited signal.
    sr, n = 48000, 48000*4
    rng = np.random.default_rng(111)
    freq = np.fft.rfftfreq(n, 1/sr)
    spectrum = rng.normal(size=len(freq)) + 1j*rng.normal(size=len(freq))
    spectrum *= (1-np.exp(-(freq/650)**4)) * np.exp(-(freq/6500)**4)
    spectrum[0] = spectrum[-1] = 0
    hiss = np.fft.irfft(spectrum, n)
    t = np.arange(n)/sr
    hiss *= 1 + .12*np.sin(2*np.pi*1.25*t) + .05*np.sin(2*np.pi*3*t)
    hiss -= np.mean(hiss)
    hiss *= .38/np.max(np.abs(hiss))
    # Flatten a short seam with a smooth raised-cosine envelope. The last and
    # first four samples are zero, giving exact value and first-slope continuity.
    edge = 96
    ramp = np.sin(np.linspace(0, math.pi/2, edge))**2
    hiss[:edge] *= ramp
    hiss[-edge:] *= ramp[::-1]
    hiss[:4] = hiss[-4:] = 0
    pcm = np.rint(hiss*32767).astype('<i2')
    with wave.open(str(output/'SFX_Flare_Hiss_Loop.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(pcm.tobytes())
    report = {'sample_rate_hz':sr,'channels':1,'bits_per_sample':16,'frames':n,'duration_seconds':n/sr,
              'seed':111,'synthesis':'NumPy PCG64 complex periodic FFT noise; 650 Hz high-pass / 6.5 kHz low-pass shaping; cyclic 1.25/3 Hz amplitude modulation',
              'seam_envelope_samples_per_end':edge,'endpoint_zero_samples_per_end':4,
              'peak_dbfs':float(20*np.log10(np.max(np.abs(pcm))/32768)),
              'rms_dbfs':float(20*np.log10(np.sqrt(np.mean((pcm.astype(float)/32768)**2))))}
    (output/'audio-build.json').write_text(json.dumps(report,indent=2)+'\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--candidate',choices=['A','B'],default='A')
    p.add_argument('--cleanup',type=Path,required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out = args.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    sys.path.insert(0,str(args.cleanup.resolve().parent))
    import cleanup_export
    obj = mesh(args.candidate)
    cleanup_export.export_fbx([obj],out/'raw.fbx')
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'candidate.blend'))
    render(obj,out/'studio.png')
    render(obj,out/'cave.png',True)
    audio(out)
    (out/'brief.txt').write_text(PROMPT+'\n')

if __name__ == '__main__': main()
