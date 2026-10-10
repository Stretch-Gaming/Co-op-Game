"""PG-1 view test. Loads L_PG_Test, starts Play As Client with N clients, and drives
real Enhanced Input (move, look, V) on client A. Checks every world. Writes /tmp/pg1/out.json."""
import json, time, traceback, unreal
N = 2  # clients: run once each with 2, 3 and 4
import os
OUT = '/tmp/pg1/out.json'
os.makedirs('/tmp/pg1', exist_ok=True)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert les.load_level('/Game/Player/Test/L_PG_Test')
settings = unreal.load_object(None, '/Script/UnrealEd.Default__LevelEditorPlaySettings')
perf = unreal.load_object(None, '/Script/UnrealEd.Default__EditorPerformanceSettings')
orig = {'play': unreal.ToolsetLibrary.get_object_properties(settings, ['PlayNetMode', 'PlayNumberOfClients', 'RunUnderOneProcess']),
        'perf': unreal.ToolsetLibrary.get_object_properties(perf, ['bThrottleCPUWhenNotForeground'])}
unreal.ToolsetLibrary.set_object_properties(settings, json.dumps({'PlayNetMode': 'PIE_Client', 'PlayNumberOfClients': N, 'RunUnderOneProcess': True}))
unreal.ToolsetLibrary.set_object_properties(perf, json.dumps({'bThrottleCPUWhenNotForeground': False}))
CHAR = unreal.load_asset('/Game/Player/Test/BP_PG_TestCharacter').generated_class()
PV = unreal.load_asset('/Game/Player/AC_PlayerView').generated_class()
IA_MOVE = unreal.load_asset('/Game/Input/Actions/IA_Move')
IA_LOOK = unreal.load_asset('/Game/Input/Actions/IA_Look')
IA_VIEW = unreal.load_asset('/Game/Core/Input/IA_ToggleView')
st = {'phase': 'start', 't0': time.monotonic(), 'deadline': time.monotonic() + 90, 'log': [], 'checks': 0, 'fails': []}

def worlds(): return unreal.EditorLevelLibrary.get_pie_worlds(True)
def server(): return next((w for w in worlds() if unreal.GameplayStatics.get_game_mode(w)), None)
def pawns(w): return list(unreal.GameplayStatics.get_all_actors_of_class(w, CHAR))
def pid(p): return p.player_state.get_editor_property('player_id') if p.player_state else -1
def pv(p): return p.get_component_by_class(PV)
def sub(p):
    lib = unreal.get_default_object(unreal.load_class(None, '/Script/Engine.SubsystemBlueprintLibrary'))
    return lib.call_method('GetLocalPlayerSubsystem', args=(p, unreal.EnhancedInputLocalPlayerSubsystem.static_class()))
def check(ok, msg):
    st['checks'] += 1
    if not ok: st['fails'].append(f"[{st['phase']}] {msg}")
def ydiff(a, b): return abs(((a - b) + 180) % 360 - 180)
def view_of(p):
    v = pv(p); arm = p.get_component_by_class(unreal.SpringArmComponent)
    return {'mode': v.get_editor_property('ViewMode') if v else None,
            'blend': round(v.get_editor_property('ViewBlend'), 3) if v else None,
            'arm': round(arm.get_editor_property('target_arm_length'), 1) if arm else None,
            'ownernosee': p.mesh.get_editor_property('owner_no_see'),
            'ctrl_yaw': p.get_editor_property('use_controller_rotation_yaw'),
            'orient': p.character_movement.get_editor_property('orient_rotation_to_movement'),
            'yaw': round(p.get_actor_rotation().yaw, 1),
            'speed': round(p.get_velocity().length(), 0), 'local': p.is_locally_controlled()}
def snap(tag):
    rows = {}
    for i, w in enumerate(worlds()):
        role = 'server' if w == server() else 'client'
        rows[f'{i}:{role}'] = {str(pid(p)): view_of(p) for p in pawns(w)}
    st['log'].append({'tag': tag, 'real_s': round(time.monotonic() - st['t0'], 2), 'game_s': round(gtime(), 2), 'worlds': rows})
    return rows
def a_in_all():
    """Client A's pawn as seen from every world."""
    return [(w, next((p for p in pawns(w) if pid(p) == st['aid']), None)) for w in worlds()]
def gnow():
    a = st.get('A')
    return unreal.GameplayStatics.get_real_time_seconds(a.get_world()) if a else time.monotonic()
def gtime():
    a = st.get('A')
    return unreal.GameplayStatics.get_time_seconds(a.get_world()) if a else 0
def go(ph): st['phase'] = ph; st['ts'] = time.monotonic(); st['gts'] = gtime(); st['frames'] = 0
def finish():
    unreal.unregister_slate_post_tick_callback(st['h'])
    les.editor_request_end_play()
    unreal.ToolsetLibrary.set_object_properties(settings, json.dumps(orig['play']))
    unreal.ToolsetLibrary.set_object_properties(perf, json.dumps(orig['perf']))
    open(OUT, 'w').write(json.dumps({'players': N, 'passed': not st['fails'] and st['phase'] == 'done', 'phase': st['phase'],
        'checks': st['checks'], 'blend_to_third_game_s': st.get('tp_done'), 'blend_to_first_game_s': st.get('fp_done'), 'fails': st['fails'], 'trace': st.get('trace'), 'log': st['log'], 'error': st.get('error')}, indent=1, default=str))

def tick(_dt):
    try:
        now = time.monotonic()
        if now > st['deadline']: st['fails'].append('timeout in ' + st['phase']); finish(); return
        ph = st['phase']; st['frames'] = st.get('frames', 0) + 1; el = (gtime() - st.get('gts', 0)) if st.get('A') else 0
        if ph == 'start':
            if not les.is_in_play_in_editor(): return
            sv = server()
            if not sv or len(worlds()) != N + 1 or any(len(pawns(w)) != N for w in worlds()): return
            owners = [p for w in worlds() if w != sv for p in pawns(w) if p.is_locally_controlled()]
            if len(owners) != N or any(pid(p) < 0 for p in owners): return
            owners.sort(key=pid)
            st['A'] = owners[0]; st['aid'] = pid(owners[0]); st['subA'] = sub(owners[0])
            check(st['subA'] is not None, 'client A has an input subsystem')
            go('settle')
        elif ph == 'settle' and el > 1.5:
            snap('initial')
            for w in worlds():
                for p in pawns(w):
                    v = view_of(p)
                    check(v['mode'] == 0, f'{w.get_name()} pid {pid(p)} starts in first person (ViewMode 0)')
                    check(v['ctrl_yaw'] and not v['orient'], f'{w.get_name()} pid {pid(p)} faces the look direction in first person')
                    if v['local']:
                        check(v['arm'] == 0 and v['ownernosee'], f'{w.get_name()} pid {pid(p)} owner camera at the eyes with body hidden: {v}')
            go('look_fp')
        elif ph == 'look_fp':
            st['subA'].inject_input_vector_for_action(IA_MOVE, unreal.Vector(0, 1, 0), [], [])
            st['subA'].inject_input_vector_for_action(IA_LOOK, unreal.Vector(1, 0, 0), [], [])
            if el > 1.2: go('check_fp')
        elif ph == 'check_fp':
            st['subA'].inject_input_vector_for_action(IA_MOVE, unreal.Vector(0, 1, 0), [], [])
            if el > 0.6:
                snap('fp_after_look')
                ctrl = st['A'].get_control_rotation().yaw
                for w, p in a_in_all():
                    check(p is not None and ydiff(p.get_actor_rotation().yaw, ctrl) < 6, f'{w.get_name()} sees A facing its look yaw {ctrl:.1f} (got {p.get_actor_rotation().yaw if p else None})')
                    check(p is not None and p.get_velocity().length() > 100, f'{w.get_name()} sees A moving')
                go('toggle_tp')
        elif ph == 'toggle_tp':
            st['subA'].inject_input_vector_for_action(IA_MOVE, unreal.Vector(0, 1, 0), [], [])
            if st["frames"] <= 3: st["subA"].inject_input_vector_for_action(IA_VIEW, unreal.Vector(1, 0, 0), [], [])
            if el < 1.0:
                sv = server(); sa = next((q for q in pawns(sv) if pid(q) == st['aid']), None)
                st.setdefault('trace', []).append((round(el, 3), pv(sa).get_editor_property('ViewMode') if sa else None,
                    pv(st['A']).get_editor_property('ViewMode'), round(pv(st['A']).get_editor_property('ViewBlend'), 3)))
            if 'tp_done' not in st and pv(st['A']).get_editor_property('ViewBlend') >= 1.0: st['tp_done'] = round(el, 3)
            if el > 1.0:
                snap('third_person')
                for w, p in a_in_all():
                    v = view_of(p)
                    check(v['mode'] == 1 and not v['ctrl_yaw'] and v['orient'], f'{w.get_name()} sees A in third person: {v}')
                    check(v['speed'] > 100, f'{w.get_name()} sees A still moving through the switch')
                    if v['local']: check(v['arm'] > 390 and not v['ownernosee'], f'A owner camera pulled back, body shown: {v}')
                for w in worlds():
                    for p in pawns(w):
                        if pid(p) != st['aid']: check(view_of(p)['mode'] == 0, f'{w.get_name()} other pawn {pid(p)} unaffected')
                yaws = [p.get_actor_rotation().yaw for _, p in a_in_all()]
                check(max(ydiff(y, yaws[0]) for y in yaws) < 6, f'all worlds agree on A facing in third person: {yaws}')
                go('turn_tp')
        elif ph == 'turn_tp':
            # strafe right while third person: body should turn to movement on every machine
            st['subA'].inject_input_vector_for_action(IA_MOVE, unreal.Vector(1, 0, 0), [], [])
            if el > 1.2:
                snap('tp_strafe')
                yaws = [p.get_actor_rotation().yaw for _, p in a_in_all()]
                check(max(ydiff(y, yaws[0]) for y in yaws) < 8, f'all worlds agree on A facing while strafing in third person: {yaws}')
                go('toggle_fp')
        elif ph == 'toggle_fp':
            st['subA'].inject_input_vector_for_action(IA_MOVE, unreal.Vector(0, 1, 0), [], [])
            if st["frames"] <= 3: st["subA"].inject_input_vector_for_action(IA_VIEW, unreal.Vector(1, 0, 0), [], [])
            if 'fp_done' not in st and pv(st['A']).get_editor_property('ViewMode') == 0 and pv(st['A']).get_editor_property('ViewBlend') <= 0.0: st['fp_done'] = round(el, 3)
            if el > 1.2:
                snap('back_to_first')
                ctrl = st['A'].get_control_rotation().yaw
                for w, p in a_in_all():
                    v = view_of(p)
                    check(v['mode'] == 0 and v['ctrl_yaw'] and not v['orient'], f'{w.get_name()} sees A back in first person: {v}')
                    check(ydiff(p.get_actor_rotation().yaw, ctrl) < 6, f'{w.get_name()} sees A facing look yaw {ctrl:.1f} again (got {v["yaw"]})')
                    if v['local']: check(v['arm'] == 0 and v['ownernosee'], f'A owner camera back at the eyes: {v}')
                go('done'); finish()
    except Exception:
        st['error'] = traceback.format_exc(); st['fails'].append('exception'); finish()
st['h'] = unreal.register_slate_post_tick_callback(tick)
les.editor_request_begin_play()
