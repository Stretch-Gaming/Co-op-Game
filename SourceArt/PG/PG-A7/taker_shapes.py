"""PG-A7 the taker: the shapes. Original Blender Python modeling with skin-modifier skeletons:
each creature is a graph of joints with radii, skinned, subdivided, roughened a little and
decimated to its triangle budget. build_taker.py turns these into the committed meshes.

Blender +Z is up, the creature faces +X, and units are metres. Every body is built with its
origin on the floor under the middle of the feet.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector, noise


class Skel:
    """A joint graph for the skin modifier: positions, (x, y) radii and edges."""

    def __init__(self):
        self.v, self.r, self.e, self.roots = [], [], [], []
        self.children = {}

    def add(self, p, r, parent=None):
        """A joint. Skin hulls fold and split where chains branch, so there are no branches:
        a second child of a joint starts a separate piece from a copy of that joint, and the
        voxel remesh fuses the overlapping pieces. With no parent it starts a piece too."""
        if parent is not None and self.children.get(parent):
            parent = self._new(self.v[parent], self.r[parent], None)
        i = self._new(p, r, parent)
        return i

    def _new(self, p, r, parent):
        self.v.append(Vector(p))
        self.r.append(r if isinstance(r, tuple) else (r, r))
        i = len(self.v) - 1
        if parent is None:
            self.roots.append(i)
        else:
            self.e.append((parent, i))
            self.children[parent] = self.children.get(parent, 0) + 1
        return i

    def chain(self, parent, pts, radii):
        out = []
        for p, r in zip(pts, radii):
            parent = self.add(p, r, parent)
            out.append(parent)
        return out

    def mirror_chain(self, parents, pts, radii):
        """The same chain on both sides: pts are given for +Y and mirrored to -Y."""
        a = self.chain(parents[0], pts, radii)
        b = self.chain(parents[1], [(x, -y, z) for x, y, z in pts], radii)
        return a, b


def spike(sk, parent, base, tip, r):
    """A tapering spine or horn, ending in a point. It's a separate piece pushed into the body
    rather than a branch of `parent`: skin hulls pinch the spine where branches meet it."""
    base, tip = Vector(base), Vector(tip)
    root = base.lerp(tip, -.6)
    mid = base.lerp(tip, .5)
    return sk.chain(None, [root, base, mid, tip], [r * .8, r, r * .55, .005])


def frame(forward, down):
    f = Vector(forward).normalized()
    d = Vector(down)
    d = (d - f * d.dot(f)).normalized()
    s = f.cross(d).normalized()
    return f, d, s


def hand(sk, wrist, palm, forward, down, scale=1.0, curl=.35, spread=.22, thumb_side=1):
    """A palm node, four long fingers and a thumb, each curled toward the palm and ending in a
    claw point. `forward` points along the fingers and `down` is the palm's facing."""
    f, d, s = frame(forward, down)
    p = sk.add(palm, .085 * scale, wrist)
    lengths = [.15 * scale, .12 * scale, .10 * scale, .07 * scale]
    radii = [.032 * scale, .028 * scale, .022 * scale, .005]
    tips = []
    for k, off in enumerate((-1.5, -.5, .5, 1.5)):
        ang = off * spread / 1.5
        dirn = (f * math.cos(ang) + s * math.sin(ang)).normalized()
        knuckle = Vector(palm) + f * .085 * scale + s * off * .042 * scale
        q = sk.add(knuckle, .034 * scale, p)
        pos = knuckle.copy()
        seg_len = [x * (1.0 if k in (1, 2) else .86) for x in lengths]
        for j, (ln, rr) in enumerate(zip(seg_len, radii)):
            bend = curl * (j + 1)
            step = (dirn * math.cos(bend) + d * math.sin(bend)).normalized()
            pos = pos + step * ln
            q = sk.add(pos, rr, q)
        tips.append(pos)
    # Thumb: out of the palm's side, curling in under it.
    side = s * thumb_side
    base = Vector(palm) + side * .07 * scale + f * .01
    q = sk.add(base, .034 * scale, p)
    pos = base
    for j, (ln, rr) in enumerate(zip([.10 * scale, .08 * scale, .06 * scale], [.028 * scale, .022 * scale, .005])):
        bend = .5 + curl * j
        step = (side * math.cos(bend) * .6 + f * .5 + d * math.sin(bend) * .7).normalized()
        pos = pos + step * ln
        q = sk.add(pos, rr, q)
    return tips


# Skin plus subdivision shrinks each joint to about 70% of its radius, so radii are given as
# the look we want and grown here. Claw and spike points stay sharp.
GROW = 1.4


def skin_object(name, sk, subdiv=2, collection=None):
    me = bpy.data.meshes.new(name + '_skel')
    me.from_pydata([tuple(v) for v in sk.v], sk.e, [])
    o = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(o)
    mod = o.modifiers.new('Skin', 'SKIN')
    mod.branch_smoothing = .4
    for i, r in enumerate(sk.r):
        sv = me.skin_vertices[0].data[i]
        sv.radius = tuple(x * GROW if x > .01 else x for x in r)
        sv.use_root = i in sk.roots
    sub = o.modifiers.new('Subdivision', 'SUBSURF')
    sub.levels = subdiv
    sub.render_levels = subdiv
    return bake_modifiers(o)


def bake_modifiers(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    old = o.data
    o.modifiers.clear()
    o.data = me
    me.name = o.name
    bpy.data.meshes.remove(old)
    return o


def clean(o):
    """Weld, drop loose bits, fill the small holes skin hulls can leave, and point every face
    outward."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-6)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    loose = [e for e in bm.edges if not e.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='EDGES')
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=64)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # The remesh treats an inside-out piece as a hole, so make sure each closed piece encloses
    # positive volume.
    for island in islands(bm):
        vol = sum(f.verts[0].co.dot(f.verts[i].co.cross(f.verts[i + 1].co))
                  for f in island for i in range(1, len(f.verts) - 1))
        if vol < 0:
            bmesh.ops.reverse_faces(bm, faces=island)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()


def islands(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f in seen:
            continue
        island, stack = [], [f]
        seen.add(f)
        while stack:
            g = stack.pop()
            island.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen:
                        seen.add(h)
                        stack.append(h)
        out.append(island)
    return out


def health(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    out = {'non_manifold_edges': sum(1 for e in bm.edges if not e.is_manifold),
           'boundary_edges': sum(1 for e in bm.edges if e.is_boundary),
           'loose_verts': sum(1 for v in bm.verts if not v.link_faces)}
    bm.free()
    return out


def remesh(o, voxel=.01):
    """Voxel-remesh into one closed shell: overlapping pieces fuse, folds and internal faces go."""
    mod = o.modifiers.new('Remesh', 'REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel
    mod.adaptivity = 0
    mod.use_smooth_shade = True
    bake_modifiers(o)
    keep_largest_parts(o, min_faces=200)


def keep_largest_parts(o, min_faces):
    """Drop tiny islands the remesh can leave behind."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    drop = [f for island in islands(bm) if len(island) < min_faces for f in island]
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bm.to_mesh(o.data)
    bm.free()


def lumpy(o, amp=.012, freq=3.0, seed=0):
    """Broad, uneven lumps along the normals: chunky, not noisy."""
    off = Vector((seed * 17.3, seed * 5.1, seed * 11.7))
    me = o.data
    me.update()
    for v in me.vertices:
        n = noise.noise(v.co * freq + off)
        v.co += v.normal * n * amp
    me.update()


def decimate_to(o, target):
    o.data.calc_loop_triangles()
    tris = len(o.data.loop_triangles)
    if tris > target:
        mod = o.modifiers.new('Decimate', 'DECIMATE')
        mod.ratio = target / tris
        bake_modifiers(o)
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def ellipsoid(name, center, radii, rot=Matrix(), segments=10, rings=6, collection=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1)
    m = Matrix.Translation(Vector(center)) @ rot.to_4x4() @ Matrix.Diagonal((*radii, 1))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    return o


def eye_pair(name, center, size=(.05, .045, .028), tilt=.35, collection=None):
    """Two slanted almond eyes, ghost white, set into the face. center is the +Y eye."""
    objs = []
    for side in (1, -1):
        c = Vector((center[0], center[1] * side, center[2]))
        rot = Matrix.Rotation(-tilt * side, 3, 'X') @ Matrix.Rotation(.25, 3, 'Y')
        objs.append(ellipsoid(f'{name}_{side}', c, (size[2], size[0], size[1] * .55), rot,
                              collection=collection))
    return objs


# ---------------------------------------------------------------------------
# Candidates. Each returns (body skeleton, eye centre for +Y, eye size).

def stalker():
    """C01 Stilt Stalker: stands on long backward-bent legs, hunched, one arm hanging to the
    knee and one reaching forward at chest height."""
    sk = Skel()
    pelvis = sk.add((-.06, 0, 1.30), (.15, .15))
    sp1, sp2, chest, hump = sk.chain(pelvis, [(-.06, 0, 1.55), (-.02, 0, 1.80), (.06, 0, 2.05), (.12, 0, 2.30)],
                                     [.12, .16, .23, .19])
    neck, head1, head2, jaw, chin = sk.chain(hump, [(.28, 0, 2.38), (.40, 0, 2.36), (.54, 0, 2.31), (.66, 0, 2.24),
                                                    (.74, 0, 2.17)], [.075, .125, .105, .06, .02])
    for side in (1, -1):
        spike(sk, head1, (.36, .07 * side, 2.46), (.04, .15 * side, 2.68), .05)
    spike(sk, hump, (.06, 0, 2.46), (-.06, 0, 2.66), .055)
    spike(sk, chest, (-.10, 0, 2.18), (-.30, 0, 2.30), .05)
    spike(sk, sp2, (-.15, 0, 1.86), (-.32, 0, 1.92), .04)
    shoulders = []
    for side in (1, -1):
        sh = sk.add((.12, .30 * side, 2.28), .11, hump)
        spike(sk, sh, (.05, .38 * side, 2.42), (-.04, .46 * side, 2.62), .05)
        shoulders.append(sh)
    # +Y arm hangs long; -Y arm reaches forward.
    el, wr = sk.chain(shoulders[0], [(.22, .46, 1.62), (.40, .46, .92)], [.08, .066])
    hand(sk, wr, (.46, .46, .78), (.25, 0, -1), (-1, 0, 0), scale=1.15, curl=.3)
    el, wr = sk.chain(shoulders[1], [(.42, -.52, 1.88), (.96, -.48, 1.68)], [.08, .066])
    hand(sk, wr, (1.09, -.47, 1.63), (1, .1, -.15), (0, 0, -1), scale=1.15, curl=.42, thumb_side=1)
    for side in (1, -1):
        hip = sk.add((-.04, .17 * side, 1.28), .12, pelvis)
        knee, ankle, ball = sk.chain(hip, [(.16, .21 * side, .82), (-.16, .22 * side, .32), (.04, .23 * side, .07)],
                                     [.085, .06, .06])
        # Toes are separate pieces from inside the foot: four-way skin branches leave holes.
        for t in (-1, 0, 1):
            sk.chain(None, [(.04, (.23 + .02 * t) * side, .07), (.20, (.23 + .05 * t) * side, .04),
                            (.30, (.23 + .07 * t) * side, .01)], [.035, .03, .005])
    return sk, (.60, .072, 2.33), (.046, .042, .032)


def shade():
    """C02 Hanging Shade: hangs in the air as if from strings, legs dangling with pointed toes,
    head drooped below the hump, one arm hanging past the knees and one reaching."""
    sk = Skel()
    pelvis = sk.add((-.08, 0, 1.45), (.14, .14))
    sp1, sp2, chest, hump = sk.chain(pelvis, [(-.10, 0, 1.70), (-.06, 0, 1.95), (.04, 0, 2.20), (.10, 0, 2.42)],
                                     [.12, .15, .20, .18])
    neck, head1, head2, jaw, chin = sk.chain(hump, [(.28, 0, 2.40), (.42, 0, 2.28), (.52, 0, 2.16), (.58, 0, 2.04),
                                                    (.60, 0, 1.94)], [.075, .115, .10, .06, .02])
    for side in (1, -1):
        spike(sk, head1, (.40, .08 * side, 2.40), (.22, .17 * side, 2.62), .05)
    spike(sk, hump, (.04, 0, 2.58), (-.10, 0, 2.80), .06)
    spike(sk, chest, (-.12, 0, 2.30), (-.34, 0, 2.42), .05)
    spike(sk, sp2, (-.20, 0, 2.00), (-.38, 0, 2.06), .04)
    shoulders = []
    for side in (1, -1):
        sh = sk.add((.10, .32 * side, 2.38), .115, hump)
        spike(sk, sh, (.02, .40 * side, 2.52), (-.08, .50 * side, 2.72), .05)
        shoulders.append(sh)
    el, wr = sk.chain(shoulders[0], [(.24, .48, 1.66), (.36, .50, .90)], [.08, .066])
    hand(sk, wr, (.40, .50, .75), (.12, .05, -1), (-1, 0, 0), scale=1.2, curl=.28)
    el, wr = sk.chain(shoulders[1], [(.46, -.56, 1.98), (1.02, -.50, 1.78)], [.08, .066])
    hand(sk, wr, (1.15, -.49, 1.73), (1, .1, -.2), (0, 0, -1), scale=1.2, curl=.45, thumb_side=1)
    for side in (1, -1):
        hip = sk.add((-.06, .15 * side, 1.42), .115, pelvis)
        knee, ankle, toe, tip = sk.chain(hip, [(.08, .18 * side, .96), (-.06, .19 * side, .50),
                                               (-.03, .19 * side, .32), (.0, .19 * side, .18)],
                                         [.08, .055, .045, .006])
    return sk, (.47, .06, 2.23), (.055, .05, .03)


def crawler():
    """C03 Hunched Crawler: walks on its long arms and short legs, shoulders high, head hanging
    low between them."""
    sk = Skel()
    pelvis = sk.add((-.55, 0, 1.05), (.15, .15))
    sp1, sp2, chest, hump = sk.chain(pelvis, [(-.38, 0, 1.30), (-.18, 0, 1.52), (.05, 0, 1.68), (.22, 0, 1.72)],
                                     [.13, .16, .21, .18])
    neck, head1, head2, jaw, chin = sk.chain(hump, [(.38, 0, 1.58), (.48, 0, 1.44), (.58, 0, 1.32), (.66, 0, 1.22),
                                                    (.70, 0, 1.12)], [.075, .115, .10, .06, .02])
    for side in (1, -1):
        spike(sk, head1, (.44, .08 * side, 1.56), (.30, .18 * side, 1.76), .05)
    for parent, base, tip, r in [(hump, (.10, 0, 1.88), (-.02, 0, 2.12), .06),
                                 (chest, (-.12, 0, 1.68), (-.30, 0, 1.92), .055),
                                 (sp1, (-.34, 0, 1.44), (-.52, 0, 1.64), .045)]:
        spike(sk, parent, base, tip, r)
    shoulders = []
    for side in (1, -1):
        sh = sk.add((.20, .32 * side, 1.70), .115, hump)
        spike(sk, sh, (.14, .40 * side, 1.84), (.04, .50 * side, 2.04), .05)
        shoulders.append(sh)
    for k, side in enumerate((1, -1)):
        fx = .90 if side > 0 else 1.05
        el, wr = sk.chain(shoulders[k], [(.42, .50 * side, 1.12), (fx - .1, .48 * side, .42)], [.08, .066])
        hand(sk, wr, (fx, .48 * side, .18), (.6, 0, -1), (0, 0, -1), scale=1.15, curl=.55, thumb_side=-side)
    for side in (1, -1):
        hip = sk.add((-.55, .17 * side, 1.0), .12, pelvis)
        knee, ankle, ball = sk.chain(hip, [(-.35, .22 * side, .60), (-.62, .23 * side, .26), (-.44, .23 * side, .07)],
                                     [.085, .06, .06])
        for t in (-1, 0, 1):
            sk.chain(ball, [(-.28, (.23 + .05 * t) * side, .04), (-.18, (.23 + .07 * t) * side, .01)], [.03, .005])
    return sk, (.60, .06, 1.42), (.05, .045, .028)


CANDIDATES = {'C01_StiltStalker': stalker, 'C02_HangingShade': shade, 'C03_HunchedCrawler': crawler}


def seat_on_surface(body, eye_c, eye_s):
    """Move the eye forward (+X) until it sits on the face, a third of its depth proud."""
    origin = Vector((eye_c[0] + .6, eye_c[1], eye_c[2]))
    hit, loc, normal, _ = body.ray_cast(origin, Vector((-1, 0, 0)), distance=1.2)
    if not hit:
        return eye_c
    return (loc.x - eye_s[2] * .3, eye_c[1], eye_c[2])


def build_body(name, builder, target=13000, collection=None, floor=True):
    sk, eye_c, eye_s = builder()
    body = skin_object(name, sk, subdiv=2, collection=collection)
    clean(body)
    remesh(body)
    lumpy(body, amp=.014, freq=2.6, seed=7)
    tris = decimate_to(body, target)
    clean(body)
    body.data.calc_loop_triangles()
    tris = len(body.data.loop_triangles)
    for p in body.data.polygons:
        p.use_smooth = True
    eye_c = seat_on_surface(body, eye_c, eye_s)
    eyes = eye_pair(name + '_Eye', eye_c, eye_s, collection=collection)
    if floor:
        # Standing candidates rest on Z 0; hanging ones keep their hover height.
        zmin = min(v.co.z for v in body.data.vertices)
        if zmin < .05:
            for o in [body] + eyes:
                for v in o.data.vertices:
                    v.co.z -= zmin
    return body, eyes, tris


def reaching_arm():
    """The arm for the wall taking. Its origin is where it leaves the wall: the arm reaches
    along +X out of a wall facing +X, with a short root buried behind the wall (X < 0) and
    shadow veins spreading over the wall's face. The open hand faces +X, fingers up and
    curling toward the victim."""
    sk = Skel()
    root = sk.add((-.38, 0, -.02), .17)
    sk.chain(root, [(-.15, 0, 0), (0, 0, 0), (.30, .02, .04), (.62, .05, .10), (.98, .05, .14),
                    (1.38, .03, .12), (1.76, 0, .08)],
             [.15, .13, .115, .10, .088, .078, .068])
    wrist = len(sk.v) - 1
    hand(sk, wrist, (1.87, 0, .13), (.45, 0, 1), (1, 0, 0), scale=1.5, curl=.38, spread=.48, thumb_side=-1)
    spike(sk, None, (.96, 0, .22), (.84, -.04, .42), .045)
    spike(sk, None, (.60, .03, .18), (.50, .0, .34), .035)
    # Shadow veins over the wall face, around the hole the arm comes out of.
    # They lie flat, half sunk into the wall plane (X 0), and wander a little as they go.
    for k, length in enumerate((.70, .52, .80, .58, .66)):
        a = k * 2 * math.pi / 5 + .4
        d = Vector((0, math.cos(a), math.sin(a)))
        side = Vector((1, 0, 0)).cross(d)
        pts, radii = [], []
        for j, t in enumerate((.0, .25, .5, .75, 1.0)):
            wiggle = math.sin(t * math.pi * 1.6 + k) * .05 * t
            pts.append(Vector((-.03 - .03 * (1 - t), 0, 0)) + d * (.10 + t * length) + side * wiggle)
            radii.append(.05 * (1 - t) + .004 * t if t < 1 else .004)
        sk.chain(None, pts, radii)
    return sk


def build_arm(name, target=5500, collection=None):
    sk = reaching_arm()
    arm = skin_object(name, sk, subdiv=2, collection=collection)
    clean(arm)
    remesh(arm, voxel=.008)
    lumpy(arm, amp=.01, freq=3.0, seed=11)
    decimate_to(arm, target)
    clean(arm)
    for p in arm.data.polygons:
        p.use_smooth = True
    arm.data.calc_loop_triangles()
    return arm, len(arm.data.loop_triangles)
