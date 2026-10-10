"""PG-A5: set the critter Blueprint defaults and place bats and rats in L_Site01_PG.

Every placement is checked against the cave as it is now: hanging bats are traced up to the
rock or beam above them, rat tracks must be flat and clear end to end, and a bat's orbit
shrinks until nothing is in its way. Rerunning replaces the actors labelled PG_A5_*. Saves only
L_Site01_PG and the two Blueprints. Run in the editor with `py <this file>` with L_Site01 open."""
import json
import math
import traceback
from pathlib import Path

import unreal

OUT = Path("/tmp/pga5_tools/out.json")
FOLDER = "PG/Critters"
HANG_HEIGHT = 23.85   # SM_Bat_Hanging, pivot at the bottom of its ears
FEET_SINK = 1.5       # toes slightly into the rock, so no gap shows

BAT_DEFAULTS = {"OrbitRadius": 250.0, "OrbitSpeed": 55.0, "BobHeight": 35.0, "FlapSpeed": 1500.0,
                "FlapAngle": 40.0, "WingLift": 10.0, "Phase": 0.0}
RAT_DEFAULTS = {"HalfLength": 130.0, "Speed": 60.0, "Phase": 0.0}

# Hanging bats, in small roosts: (x, y, yaw) in cm. Site 1 layout: spawn cavern beams at X -650,
# 50 and 750; plate hall ceiling 10 m; trap corridor 4 m; altar cavern 12 m.
HANGING = [
    (-650, 320, 10), (-650, 348, 75), (-650, 377, -30),           # spawn, west beam
    (50, -480, 140), (50, -452, 200),                              # spawn, middle beam
    (750, 610, -60),                                               # spawn, east beam
    (750, 575, 200), (-650, -380, 80), (-650, -352, 160),          # spawn, more on the beams: the cavern's
                                                                   # rock ceiling hangs below its collision
    (3500, 1000, 0), (3530, 1032, 95), (3468, 1040, 210),          # plate hall, north-west
    (4620, -1080, 40), (4652, -1060, 160),                         # plate hall, south-east
    (6560, 120, 30), (6590, 140, 150),                             # trap corridor, before the darts
    (9300, 880, 15), (9330, 912, 120), (9278, 935, 250), (9350, 870, 300),   # altar, north-west
    (10620, -820, 60), (10655, -845, 190),                         # altar, south-east
]
# Flying bats: (x, y, z, radius, speed in deg/s, phase in s).
FLYING = [
    (0, 0, 480, 380, 45, 0.0), (350, -250, 520, 220, -62, 2.3),            # spawn cavern
    (4000, 0, 760, 520, 38, 1.1),                                          # plate hall
    (10000, 0, 880, 460, 50, 3.7), (9900, 150, 1000, 300, -36, 0.6),       # altar cavern
]
# Rats: (x, y, yaw, half length, viewpoint x, y). The track runs along the actor's X, and starts
# near a wall. It moves toward the viewpoint, a spot players stand in, until the floor is flat,
# nothing is in the way, and both ends can be seen from there (so no rat runs behind a fence).
RATS = [
    (-400, 960, 0, 120, 0, 0), (450, -810, 0, 170, 0, 0),      # spawn cavern: inside the north fence, beside the rails
    (4000, -1360, 0, 170, 4000, 0),                            # plate hall, south wall
    (5850, -150, 0, 90, 5850, 0),                              # trap corridor, south wall
    (9500, -1030, 0, 140, 10000, 0), (10500, 1030, 180, 130, 10000, 0),   # altar cavern
]

world = unreal.EditorLevelLibrary.get_editor_world()
log = {"hanging": [], "flying": [], "rats": [], "skipped": []}


def hit(a, b, radius=0.0):
    if radius:
        h = unreal.SystemLibrary.sphere_trace_single(world, a, b, radius, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     True, [], unreal.DrawDebugTrace.NONE, True)
    else:
        h = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                   True, [], unreal.DrawDebugTrace.NONE, True)
    if h is None:
        return None
    t = h.to_tuple()
    return t[4] if t[0] else None


def V(x, y, z):
    return unreal.Vector(float(x), float(y), float(z))


def tag(actor, label):
    actor.set_actor_label(label)
    actor.set_folder_path(FOLDER)


def set_defaults(path, values):
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    for k, v in values.items():
        cdo.set_editor_property(k, v)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp


def place_hanging(i, x, y, yaw):
    up = hit(V(x, y, 150), V(x, y, 3000))
    if up is None:
        log["skipped"].append(["hanging", x, y, "no ceiling"])
        return
    z = up.z - HANG_HEIGHT + FEET_SINK
    a = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y, z), unreal.Rotator(0, 0, yaw))
    comp = a.static_mesh_component
    comp.set_static_mesh(unreal.load_asset("/Game/Player/Art/SM_Bat_Hanging"))
    comp.set_collision_profile_name("NoCollision")
    comp.set_editor_property("generate_overlap_events", False)
    comp.set_editor_property("can_ever_affect_navigation", False)
    tag(a, f"PG_A5_BatHanging_{i:02d}")
    log["hanging"].append([a.get_actor_label(), round(x), round(y), round(z, 1)])


def clear_ring(cx, cy, z, r, bob):
    for zz in (z - bob, z + bob):
        pts = [V(cx + r * math.cos(k * math.pi / 8), cy + r * math.sin(k * math.pi / 8), zz) for k in range(17)]
        for p, q in zip(pts, pts[1:]):
            if hit(p, q, 30.0) is not None:
                return False
    return True


def place_flying(i, bat_cls, x, y, z, r, speed, phase):
    bob = BAT_DEFAULTS["BobHeight"]
    while r >= 120 and not clear_ring(x, y, z, r, bob):
        r *= 0.85
    if r < 120:
        log["skipped"].append(["flying", x, y, z, "no clear orbit"])
        return
    a = unreal.EditorLevelLibrary.spawn_actor_from_class(bat_cls, V(x, y, z), unreal.Rotator(0, 0, 0))
    a.set_editor_property("OrbitRadius", float(round(r)))
    a.set_editor_property("OrbitSpeed", float(speed))
    a.set_editor_property("Phase", float(phase))
    tag(a, f"PG_A5_BatFlying_{i:02d}")
    log["flying"].append([a.get_actor_label(), x, y, z, round(r), speed])


def seen(view, p):
    """True if nothing blocks the line from the viewpoint to just above p."""
    target = V(p.x, p.y, p.z + 6)
    h = hit(view, target)
    return h is None or (h - target).length() < 3


def place_rat(i, rat_cls, x, y, yaw, half, vx, vy):
    d = V(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0)
    # Players stand all over a room, so an end counts as seen if any of five spots sees it.
    views = [V(vx + ox, vy + oy, 160) for ox, oy in ((0, 0), (400, 0), (-400, 0), (0, 400), (0, -400))]
    toward = V(vx - x, vy - y, 0)
    dist = toward.length()
    toward = toward / max(dist, 1)
    for step in range(int(dist // 40) + 1):
        cx, cy = x + toward.x * 40 * step, y + toward.y * 40 * step
        ends = [V(cx - d.x * half, cy - d.y * half, 0), V(cx, cy, 0), V(cx + d.x * half, cy + d.y * half, 0)]
        floors = [hit(V(p.x, p.y, 120), V(p.x, p.y, -200)) for p in ends]
        if floors[1] is None or any(f is None or abs(f.z - floors[1].z) > 4 for f in floors):
            continue
        fz = floors[1].z
        if hit(V(ends[0].x, ends[0].y, fz + 13), V(ends[2].x, ends[2].y, fz + 13), 10.0) is not None:
            continue
        if not all(any(seen(v, V(p.x, p.y, fz)) for v in views) for p in ends):
            continue
        a = unreal.EditorLevelLibrary.spawn_actor_from_class(rat_cls, V(cx, cy, fz), unreal.Rotator(0, 0, yaw))
        a.set_editor_property("HalfLength", float(half))
        a.set_editor_property("Phase", float(i * 1.7))
        tag(a, f"PG_A5_Rat_{i:02d}")
        log["rats"].append([a.get_actor_label(), round(cx), round(cy), round(fz, 1), yaw, half, step * 40])
        return
    log["skipped"].append(["rat", x, y, "no flat clear track"])


def main():
    bat = set_defaults("/Game/Player/Critters/BP_CaveBat", BAT_DEFAULTS)
    rat = set_defaults("/Game/Player/Critters/BP_CaveRat", RAT_DEFAULTS)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.set_current_level_by_name("L_Site01_PG"):
        raise RuntimeError("couldn't make L_Site01_PG current")
    if les.get_current_level().get_outermost().get_name() != "/Game/Player/L_Site01_PG":
        raise RuntimeError("current level isn't L_Site01_PG")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    old = [a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("PG_A5_")]
    for a in old:
        if a.get_outermost().get_name() != "/Game/Player/L_Site01_PG":
            raise RuntimeError(f"{a.get_actor_label()} is outside L_Site01_PG")
        eas.destroy_actor(a)
    log["removed"] = len(old)
    for i, h in enumerate(HANGING, 1):
        place_hanging(i, *h)
    for i, f in enumerate(FLYING, 1):
        place_flying(i, bat.generated_class(), *f)
    for i, r in enumerate(RATS, 1):
        place_rat(i, rat.generated_class(), *r)
    placed = [a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("PG_A5_")]
    log["outside_pg"] = [a.get_actor_label() for a in placed if a.get_outermost().get_name() != "/Game/Player/L_Site01_PG"]
    if log["outside_pg"]:
        raise RuntimeError(f"placed outside L_Site01_PG: {log['outside_pg']}")
    pg = unreal.find_package("/Game/Player/L_Site01_PG")
    log["saved"] = unreal.EditorLoadingAndSavingUtils.save_packages([pg], only_dirty=False)


try:
    main()
except Exception:
    log["error"] = traceback.format_exc()
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(log, indent=1))
