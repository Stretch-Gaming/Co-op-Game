"""Read-only editor observer. Primary supplies ROOT and ARGS; never starts PIE."""
import builtins
import collections
import datetime
import importlib.util
import json
import math
import os
import pathlib
import platform
import time
import traceback
import unreal as ue

EXPECTED_ROOT = pathlib.Path('C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game').resolve()
MAP = '/Game/Maps/L_ConnectedRoomMaze'
LEVELS = {MAP, '/Game/Hazards/L_Site01_HZ', '/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze'}
assert pathlib.Path(ROOT).resolve() == EXPECTED_ROOT, 'Wrong checkout'
assert pathlib.Path(ue.Paths.project_dir()).resolve() == EXPECTED_ROOT, 'Wrong editor project'
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3'), 'Requires Unreal 5.8.3'
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name() == MAP, 'Open connected preview explicitly'
assert {l.get_outermost().get_name() for l in ue.EditorLevelUtils.get_levels(world)} == LEVELS, 'Unexpected loaded levels'
KEY = '_coop_quality_performance_observer'
active = getattr(builtins, KEY, None)
if ARGS.get('cancel'):
    assert active, 'No active performance observer'
    active['finish']('cancelled')
    RESULT = {'cancelled': True}
else:
    assert not active, 'Observer already running; cancel it before starting another'
    command_line = ue.SystemLibrary.get_command_line()
    assert ARGS.get('census_only') or '-nullrhi' not in command_line.lower(), 'NullRHI permits census only, not timing claims'
    spec = importlib.util.spec_from_file_location('coop_quality_timing', EXPECTED_ROOT / 'Tools/quality/performance/stats.py')
    timing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(timing)
    output = EXPECTED_ROOT / 'Saved/QualityPerformance'
    output.mkdir(parents=True, exist_ok=True)
    name = ARGS.get('report', 'performance-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.json')
    assert pathlib.Path(name).name == name and name.endswith('.json'), 'Report must be a plain .json filename'
    report = output / name
    assert not report.exists(), 'Choose a fresh report filename'
    context = str(ARGS.get('context', 'unspecified; primary must describe view, movement, PIE, foreground state and other GPU work'))
    def safe(fn):
        try:
            return fn()
        except Exception as exc:
            return {'unavailable': str(exc)}

    def load_context():
        result = {'system': platform.platform(), 'cpu_count': os.cpu_count(), 'load_average': safe(lambda: os.getloadavg())}
        try:
            import psutil
            result.update(cpu_percent=psutil.cpu_percent(interval=None), memory_available_bytes=psutil.virtual_memory().available)
        except ImportError:
            result['cpu_percent'] = 'unavailable: psutil absent; no dependency installed'
        return result

    inventory_start = time.perf_counter()
    actors = list(ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors())
    census = collections.Counter()
    rows = []
    for actor in actors:
        census['actors'] += 1
        for component in actor.get_components_by_class(ue.ActorComponent):
            cls = component.get_class().get_name()
            census['component:' + cls] += 1
            row = {'actor': actor.get_actor_label(), 'component': component.get_name(), 'class': cls}
            if isinstance(component, ue.PrimitiveComponent):
                row['collision'] = str(safe(component.get_collision_enabled))
                row['casts_shadow'] = safe(lambda: component.get_editor_property('cast_shadow'))
            if isinstance(component, ue.MeshComponent):
                row['material_slots_proxy'] = safe(component.get_num_materials)
                if hasattr(component, 'get_instance_count'):
                    row['instances'] = safe(component.get_instance_count)
                if hasattr(component, 'get_num_sections'):
                    row['sections'] = safe(component.get_num_sections)
            if isinstance(component, ue.LightComponent):
                row.update({p: safe(lambda p=p: str(component.get_editor_property(p))) for p in ('mobility','intensity','cast_shadows')})
                row['attenuation_radius'] = safe(lambda: component.get_editor_property('attenuation_radius'))
            rows.append(row)
    census_ms = (time.perf_counter() - inventory_start) * 1000
    settings = {name: safe(lambda name=name: ue.SystemLibrary.get_console_variable_float_value(name)) for name in
                ('t.MaxFPS','r.VSync','r.ScreenPercentage','r.DynamicRes.OperationMode','r.RayTracing','r.Lumen.DiffuseIndirect.Allow','r.Shadow.Virtual.Enable')}
    observed_pie = list(ue.EditorLevelLibrary.get_pie_worlds(True))
    pie_worlds = [w.get_path_name() for w in observed_pie]
    assert all(p.endswith('.L_ConnectedRoomMaze') for p in pie_worlds), 'Unexpected PIE map'
    initial_load = load_context()
    state = {'handle': None, 'window': timing.Window(time.monotonic()), 'native_ms': [], 'wall_ms': [], 'observer_ms': [], 'previous': None,
             'pie_delta_ms': {p: [] for p in pie_worlds}}

    def finish(status, error=None):
        if state['window'].closed:
            return
        try:
            state['window'].close(lambda: ue.unregister_slate_post_tick_callback(state['handle']) if state['handle'] is not None else None)
        except Exception:
            status = 'cleanup_error'
            error = (error or '') + '\n' + traceback.format_exc()
        finally:
            setattr(builtins, KEY, None)
        payload = {'status': status, 'error': error, 'project': str(EXPECTED_ROOT), 'map': MAP, 'context': context,
                   'utc_finished': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'engine': ue.SystemLibrary.get_engine_version(),
                   'method': 'Native Slate post-tick delta and wall intervals; editor cadence, NOT GPU/game-thread timing or standalone FPS. Observer cost is reported separately, not subtracted.',
                   'warmup_seconds': 30, 'measurement_seconds': 30, 'wall_elapsed_seconds': time.monotonic()-state['window'].start,
                   'native_tick': timing.summary(state['native_ms']), 'wall_tick': timing.summary(state['wall_ms']),
                   'observer_cost': timing.summary(state['observer_ms']), 'raw_samples': {k: state[k] for k in ('native_ms','wall_ms','observer_ms')},
                   'settings': settings, 'pie_worlds': pie_worlds, 'load_start': initial_load, 'load_end': load_context(),
                   'command_line': command_line, 'census_only': bool(ARGS.get('census_only')),
                   'pie_world_delta': {p: timing.summary(v) for p,v in state['pie_delta_ms'].items()},
                   'pie_world_delta_raw_ms': state['pie_delta_ms'],
                   'pie_delta_limits': 'World simulation delta sampled at Slate callbacks; may be capped/scaled/paused or repeated between game frames. Not GPU time or isolated thread work.',
                   'inventory_cost_ms': census_ms, 'census': dict(census), 'components': rows,
                   'draw_estimate_limits': 'Material slots/sections/instances are candidate counts only; not visible draws, GPU cost, triangles or a proven bottleneck.'}
        report.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        ue.log('Performance observer finished: ' + status + ' ' + str(report))

    def tick(delta):
        entered = time.perf_counter()
        try:
            assert pathlib.Path(ue.Paths.project_dir()).resolve() == EXPECTED_ROOT, 'Project changed'
            assert world == ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(), 'Editor world changed'
            assert world.get_outermost().get_name() == MAP, 'Map changed'
            assert [w.get_path_name() for w in ue.EditorLevelLibrary.get_pie_worlds(True)] == pie_worlds, 'PIE worlds changed'
            now = time.monotonic()
            phase = state['window'].phase(now)
            if phase in ('finish','timeout'):
                finish('complete' if phase == 'finish' else 'timeout')
                return
            if phase == 'measure' and state['previous'] is not None:
                assert math.isfinite(float(delta)) and float(delta) >= 0, 'Invalid native tick delta'
                state['native_ms'].append(float(delta)*1000)
                state['wall_ms'].append((now-state['previous'])*1000)
                for w in observed_pie:
                    value = float(ue.GameplayStatics.get_world_delta_seconds(w))*1000
                    assert math.isfinite(value) and value >= 0, 'Invalid PIE world delta'
                    state['pie_delta_ms'][w.get_path_name()].append(value)
            state['previous'] = now
            if phase == 'measure':
                state['observer_ms'].append((time.perf_counter()-entered)*1000)
        except Exception:
            finish('error', traceback.format_exc())

    if ARGS.get('census_only'):
        finish('census_only')
        RESULT = {'report': str(report), 'census_only': True}
    else:
        state['handle'] = ue.register_slate_post_tick_callback(tick)
        setattr(builtins, KEY, {'finish': finish})
        RESULT = {'queued': str(report), 'warmup_seconds': 30, 'measurement_seconds': 30, 'observer': KEY}
