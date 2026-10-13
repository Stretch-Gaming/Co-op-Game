"""Parent-only native CrystalLock Lit acceptance; execute inside an already running PIE.

ARGS = {'players': 2, 'profile': 'joining'} or
       {'players': 4, 'profile': 'host_split'}; optional timeout (default 180 seconds).
Optional ARGS.capture_shots=True requests native Shot SHOWUI at stable Lit edges;
requests/files alone make no pixel, viewport-identity or readability claim.
No PIE starts/stops, compilation, package saves, direct lock-state writes, ApplyLock,
lightable messages, or headlamp component mutation calls occur in this script.
The only gameplay stimulus is IA_Headlamp (F) injected through the actual owner's
Enhanced Input local-player subsystem. Starting from fresh Lobby, the parent-
authorized authoritative GameMode fixture chain StartRound(1), ClearRound(),
StartRound(2), ClearRound() initializes enabled locks; clearing Round 2 starts 3.
All four calls run in one callback before Round 2 director/taking timers tick.
This is a disclosed isolated fixture, not proof of the arrival route or Round 3
completion. Server approach teleports and owning-controller aim are restored.

The pre-import read-only inspection supplies the old sphere root/collision/bounds
reference. Runtime braziers are also snapshotted before input and must stay equal.
Outputs are external, under /tmp/hc-a4-crystal-lock/runtime-evidence. Merely writing
or compiling this Python source does not run it. The editor owner invokes it.
"""

import importlib.util
import json
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

PRIMARY = Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary').resolve()
EVIDENCE = Path('/tmp/hc-a4-crystal-lock/runtime-evidence')
SUPPORT_PATH = Path('/tmp/coop-audit/ghost_runtime_support.py')
SUPPORT_NAME = 'hc_a4_crystal_lock_native_runtime_support_v1'
INSPECTION = Path('/tmp/hc-a4-crystal-lock/unreal-inspection.json')
LOCK_PATH = '/Game/Puzzles/BP_CrystalLock'
VISUAL_PREFIX = 'HC_CrystalLockVisual'
VISUAL_MESH = '/Game/Puzzles/Art/CrystalLock/SM_CrystalLock.SM_CrystalLock'
MATERIAL = '/Game/Puzzles/Art/CrystalLock/M_CrystalLockCrystal.M_CrystalLockCrystal'
SCALAR_HEADER = '/Volumes/CoopBuild/UnrealEngine/UE_5.8/Engine/Source/Runtime/Engine/Public/Materials/MaterialInstanceDynamic.h:55'


def utc():
    return datetime.now(timezone.utc).isoformat()


def persist(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def run(args):
    # Persist before even importing Unreal or checking ARGS, so missing PIE,
    # unsupported profiles, missing imported assets and module failures leave proof.
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    suffix = re.sub(r'[^A-Za-z0-9_-]', '_', str(args.get('profile', 'unspecified')) + '-' + str(args.get('players', 'unspecified')))
    receipt_path = EVIDENCE / ('startup-receipt-' + suffix + '.json')
    report_path = EVIDENCE / ('crystal-lock-lit-' + suffix + '.json')
    receipt = {'started_utc': utc(), 'status': 'starting', 'stage': 'preflight',
               'args': dict(args), 'report': str(report_path), 'stage_history': [],
               'native_test_executed': False, 'runtime_acceptance_pending': True}
    persist(receipt_path, receipt)
    persist(report_path, {'passed': False, 'status': 'starting', 'started_utc': receipt['started_utc'],
                          'runtime_acceptance_pending': True, 'startup_receipt': str(receipt_path)})
    h = None
    observations = []
    inputs = []
    cleanup_rows = []
    cleanup_done = set()
    initial_poses = {}
    runtime_baseline = {}
    round_states = []
    scalar_api = set()
    shots = []
    capture_shots = args.get('capture_shots', False) is True

    def stage(name, detail=None):
        receipt['stage'] = name
        receipt['stage_history'].append({'stage': name, 'utc': utc(), 'detail': detail})
        persist(receipt_path, receipt)

    try:
        import unreal as ue
        assert Path(ue.Paths.project_dir()).resolve() == PRIMARY, 'Exact primary checkout required'
        assert (args.get('profile'), int(args.get('players', 0))) in (('joining', 2), ('host_split', 4)), 'Required profiles are joining/2 and host_split/4'
        assert SUPPORT_PATH.is_file(), 'Parent-provided native Harness missing: ' + str(SUPPORT_PATH)
        assert INSPECTION.is_file(), 'Pre-import sphere/brazier inspection missing'
        before = json.loads(INSPECTION.read_text())
        assert before['project'] == str(PRIMARY), 'Inspection belongs to a different checkout'
        inspected = {row['path'].rsplit('.', 1)[-1]: row for row in before['actors']}
        assert len(inspected) == len(before['actors']), 'Inspection actor names must be unique'
        assert len([row for row in inspected.values() if not row['Brazier']]) == 2
        assert len([row for row in inspected.values() if row['Brazier']]) == 2
        # The namespace is private and stable across invocations, preserving its
        # own active-harness guard without reusing/reloading a generic "harness".
        support = sys.modules.get(SUPPORT_NAME)
        if support is None:
            spec = importlib.util.spec_from_file_location(SUPPORT_NAME, str(SUPPORT_PATH))
            assert spec and spec.loader
            support = importlib.util.module_from_spec(spec)
            sys.modules[SUPPORT_NAME] = support
            try:
                spec.loader.exec_module(support)
            except BaseException:
                sys.modules.pop(SUPPORT_NAME, None)
                raise
        assert Path(support.__file__).resolve() == SUPPORT_PATH.resolve()
        assert not support._ACTIVE_HARNESSES, 'An HC-A4 native gate is already active'
        native_args = dict(args)
        native_args.setdefault('timeout', 180)
        h = support.Harness(native_args, 'hc-a4-crystal-lock-lit')
        h.queue = EVIDENCE
        h.report = report_path
        # Distinct PIE worlds can share UWorld.GetName; package/object paths
        # uniquely identify peer baselines and their locally bound MIDs.
        assert len({world.get_path_name() for world in h.worlds}) == len(h.worlds)
        for inventory, world in zip(h.world_inventory, h.worlds):
            inventory['world_path'] = world.get_path_name()
        receipt['pie_settings'] = h.settings
        receipt['world_inventory'] = h.world_inventory
        receipt['player_ids'] = h.ids
        lobby_round = h.round()
        assert lobby_round['phase'] == 0, 'Fresh quiet Lobby required before the authorized isolated Round 3 fixture'
        round_states.append({'stage': 'fresh Lobby before authorized initializer', 'state': lobby_round})
        lock_asset = ue.load_asset(LOCK_PATH)
        assert lock_asset and ue.load_asset(VISUAL_MESH.split('.')[0]) and ue.load_asset(MATERIAL.split('.')[0]), 'Complete parent import before invoking this helper'
        lock_class = lock_asset.generated_class()
        locks = sorted(ue.GameplayStatics.get_all_actors_of_class(h.server, lock_class), key=lambda actor: actor.get_name())
        assert {actor.get_name() for actor in locks} == set(inspected), 'Loaded native lock roster differs from the pre-import inspection'
        beams = []
        braziers = [actor for actor in locks if actor.get_editor_property('Brazier')]
        assert not list(ue.GameplayStatics.get_all_actors_of_class(h.server, h.classes['flare'])), 'Fresh Lobby must have no active flares'
        assert all(not h.prop(h.locals[pid], 'view', 'bHeadlampOn') for pid in h.ids), 'Fresh Lobby must start with every owning headlamp off; do not silently normalize an old session'
        for world in h.worlds:
            for pawn in h.pawns(world):
                assert not h.prop(pawn, 'health', 'bDead') and not pawn.call_method('IsCarryingHeavy') and not pawn.get_editor_property('bTakenProtected'), 'Fresh unencumbered living owners required'
                assert not h.prop(pawn, 'view', 'bHeadlampOn'), 'Wait for fresh headlamp-off replication'

        def vec(value):
            return [float(value.x), float(value.y), float(value.z)]

        def rot(value):
            return [float(value.pitch), float(value.yaw), float(value.roll)]

        def close(actual, expected, tolerance=.1):
            return len(actual) == len(expected) and all(abs(float(a) - float(b)) <= tolerance for a, b in zip(actual, expected))

        def round_for(world):
            state = ue.GameplayStatics.get_game_state(world).get_editor_property('RoundState')
            return {'world': world.get_path_name(),
                    'index': int(state.get_editor_property('Index_11_91104438409472A6DD374BADC8DC29B1')),
                    'attempt': int(state.get_editor_property('Attempt_12_246832B34F4E147660E8729696BDD44A')),
                    'phase': int(re.search(r'Phase_[^=]+=NewEnumerator(\d+)', state.export_text())[1])}

        def materials(component):
            return [item.get_path_name() if item else None for item in component.get_materials()]

        def visual_of(actor):
            visuals = [component for component in actor.get_components_by_class(ue.StaticMeshComponent) if component.get_name().startswith(VISUAL_PREFIX)]
            assert len(visuals) == 1, (actor.get_path_name(), 'Exactly one imported local visual required')
            return visuals[0]

        def scalar(mid):
            assert mid and ue.SystemLibrary.is_valid(mid) and isinstance(mid, ue.MaterialInstanceDynamic), 'Local CrystalLockMID missing; presentation initialization is not proven'
            method = getattr(mid, 'get_scalar_parameter_value', None)
            if method:
                scalar_api.add('MaterialInstanceDynamic.get_scalar_parameter_value')
                return float(method('Lit'))
            # Installed 5.8 header declares this UFUNCTION with ScriptName
            # GetScalarParameterValue. This fallback is the same read-only API.
            scalar_api.add('MaterialInstanceDynamic.call_method(K2_GetScalarParameterValue)')
            return float(mid.call_method('K2_GetScalarParameterValue', args=('Lit',)))

        def geometry(actor):
            root = actor.static_mesh_component
            assert isinstance(actor, ue.StaticMeshActor), 'Legacy StaticMeshActor inheritance changed'
            assert actor.get_editor_property('root_component') == root, 'Legacy mesh is no longer the actor root'
            mesh = root.get_editor_property('static_mesh')
            center, extent = actor.get_actor_bounds(False)
            bound = mesh.get_bounds()
            return {'root_name': root.get_name(), 'root_mesh': mesh.get_path_name(),
                    'root_collision_profile': str(root.get_collision_profile_name()),
                    'root_collision_enabled': str(root.get_collision_enabled()),
                    'root_configured_collision_enabled': str(root.get_editor_property('body_instance').get_editor_property('collision_enabled')),
                    'actor_collision_enabled': bool(actor.get_actor_enable_collision()),
                    'actor_location': vec(actor.get_actor_location()), 'actor_scale': vec(actor.get_actor_scale3d()),
                    'actor_rotation': rot(actor.get_actor_rotation()),
                    'root_relative_location': vec(root.get_editor_property('relative_location')),
                    'root_relative_scale': vec(root.get_editor_property('relative_scale3d')),
                    'root_materials': materials(root),
                    'root_visible': bool(root.get_editor_property('visible')),
                    'mesh_local_origin': vec(bound.origin), 'mesh_local_extent': vec(bound.box_extent),
                    'world_origin': vec(center), 'world_dimensions': [2 * value for value in vec(extent)]}

        def lock_row(world, server_actor):
            actor = h.actor_peer(world, server_actor)
            visual = visual_of(actor)
            mid = actor.get_editor_property('CrystalLockMID')
            is_brazier = bool(actor.get_editor_property('Brazier'))
            return {'world': world.get_path_name(), 'actor': actor.get_name(), 'path': actor.get_path_name(),
                    'brazier': is_brazier, 'enabled': bool(actor.get_editor_property('Enabled')),
                    'lock_slot': int(actor.get_editor_property('LockSlot')),
                    'lit': bool(actor.get_editor_property('Lit')), 'source_count': int(actor.get_editor_property('SourceCount')),
                    'geometry': geometry(actor),
                    'visual_mesh': visual.get_editor_property('static_mesh').get_path_name() if visual.get_editor_property('static_mesh') else None,
                    'visual_visible': bool(visual.get_editor_property('visible')),
                    'visual_collision_enabled': str(visual.get_collision_enabled()),
                    'visual_relative_location': vec(visual.get_editor_property('relative_location')),
                    'visual_relative_scale': vec(visual.get_editor_property('relative_scale3d')),
                    'visual_absolute_scale': bool(visual.get_editor_property('absolute_scale')),
                    'visual_materials': materials(visual),
                    'mid': mid.get_path_name() if mid else None,
                    'mid_is_slot_1': bool(mid and visual.get_material(1) == mid),
                    'mid_lit_scalar': None if is_brazier else scalar(mid)}

        def validate_import(row):
            original = inspected[row['actor']]
            g = row['geometry']
            assert row['brazier'] == original['Brazier']
            for key in ('root_mesh', 'root_collision_profile', 'root_materials'):
                assert g[key] == original[key], (row['world'], row['actor'], key, g[key], original[key])
            assert g['root_configured_collision_enabled'] == original['root_collision_enabled'], row
            # get_collision_enabled reflects actor suppression on disabled locks.
            # Enabled locks must retain the inspected root's effective collision.
            if row['enabled']:
                assert g['root_collision_enabled'] == original['root_collision_enabled'], row
                assert g['actor_collision_enabled'], row
            for key in ('actor_location', 'actor_scale', 'root_relative_location', 'root_relative_scale', 'world_origin', 'world_dimensions'):
                assert close(g[key], original[key]), (row['world'], row['actor'], key, g[key], original[key])
            assert close(g['actor_rotation'], [0, 0, 0], .001), row
            assert close(g['mesh_local_origin'], original['mesh_local_bounds']['origin']), row
            assert close(g['mesh_local_extent'], original['mesh_local_bounds']['extent']), row
            assert close(row['visual_relative_location'], [0, 0, -50], .001), row
            assert close(row['visual_relative_scale'], [1, 1, 1], .001) and row['visual_absolute_scale'], row
            if row['brazier']:
                assert g['root_visible'] == original['root_visible'] and not row['visual_visible'] and row['mid'] is None, 'Brazier presentation changed'
            else:
                assert row['visual_mesh'] == VISUAL_MESH, row
                assert row['visual_collision_enabled'] == str(ue.CollisionEnabled.NO_COLLISION), row
                assert g['root_mesh'] == '/Engine/BasicShapes/Sphere.Sphere', row
                assert not g['root_visible'] and row['visual_visible'] and row['mid_is_slot_1'], row

        def record_locks():
            return [lock_row(world, actor) for world in h.worlds for actor in locks]

        initial_rows = record_locks()
        for row in initial_rows:
            validate_import(row)
            assert not row['lit'] and row['source_count'] == 0, 'Fresh Lobby starts with no lock light sources'
            if not row['brazier']:
                assert abs(row['mid_lit_scalar']) <= .0001, row
        mids = [row['mid'] for row in initial_rows if not row['brazier']]
        assert len(set(mids)) == len(mids), 'Each peer must own its distinct local CrystalLockMID'
        observations.append({'gate': 'fresh Lobby imported presentation baseline', 'rows': initial_rows})
        for pid in h.ids:
            pawn = h.pawn(h.server, pid)
            initial_poses[pid] = {'position': vec(pawn.get_actor_location()), 'rotation': rot(pawn.get_actor_rotation()),
                                  'velocity': vec(pawn.character_movement.velocity),
                                  'owner_control_rotation': rot(h.locals[pid].get_controller().get_control_rotation())}

        def restore_owner(pid):
            if pid in cleanup_done:
                return
            saved = initial_poses[pid]
            pawn = h.pawn(h.server, pid)
            h.aims.pop(pid, None)
            controller = h.locals[pid].get_controller()
            controller.set_control_rotation(ue.Rotator(pitch=saved['owner_control_rotation'][0], yaw=saved['owner_control_rotation'][1], roll=saved['owner_control_rotation'][2]))
            pawn.set_actor_location(ue.Vector(*saved['position']), False, True)
            pawn.set_actor_rotation(ue.Rotator(pitch=saved['rotation'][0], yaw=saved['rotation'][1], roll=saved['rotation'][2]), True)
            pawn.character_movement.velocity = ue.Vector(*saved['velocity'])
            actual_position = vec(pawn.get_actor_location())
            actual_rotation = rot(pawn.get_actor_rotation())
            actual_control = rot(controller.get_control_rotation())
            assert close(actual_position, saved['position'], .01) and close(actual_rotation, saved['rotation'], .01)
            assert close(actual_control, saved['owner_control_rotation'], .01)
            cleanup_rows.append({'player_id': pid, 'stage': h.phase, 'server_pose_restored': True,
                                 'owning_controller_rotation_restored': True, 'position': actual_position,
                                 'rotation': actual_rotation, 'control_rotation': actual_control})
            cleanup_done.add(pid)

        def cleanup_poses():
            h.aims.clear()
            errors = []
            for pid in initial_poses:
                try:
                    restore_owner(pid)
                except Exception:
                    errors.append({'player_id': pid, 'error': traceback.format_exc()})
            if errors:
                cleanup_rows.extend(errors)
                raise AssertionError('Failed restoring native fixture poses: ' + str(errors))

        h.cleanup.append(cleanup_poses)
        old_finish = h.finish

        def finish(passed, error=None):
            if h.finished:
                return
            # Capture final observed state before restoration. Failure snapshots
            # are best-effort and never hide the original failure or cleanup.
            final_rows = None
            final_read_error = None
            try:
                final_rows = record_locks()
            except Exception:
                final_read_error = traceback.format_exc()
            result = old_finish(passed, error)
            if result:
                # The shared support's mixed Mac/packet flag cannot describe
                # native Mac PIE separately from untested network emulation.
                for shot in shots:
                    candidates = [Path(shot['requested_file']), Path(shot['requested_file']).with_suffix('.exr')]
                    shot['files_present'] = [{'path': str(path), 'bytes': path.stat().st_size} for path in candidates if path.is_file()]
                result.pop('mac_or_packet_emulation_tested', None)
                result.update({'started_utc': receipt['started_utc'], 'finished_utc': utc(),
                               'scope': 'Fresh Lobby then isolated authorized server GameMode fixture StartRound1 -> ClearRound1 -> StartRound2 -> ClearRound2 (auto starts3) in one callback; native owning F headlamp on/off; no arrival-route or full Round 3 completion claim',
                               'pre_import_inspection': str(INSPECTION), 'fresh_lobby_baseline': initial_rows,
                               'runtime_baseline': list(runtime_baseline.values()), 'round_state_observations': round_states,
                               'light_observations': observations, 'input_edges': inputs,
                               'restored_fixture_poses': cleanup_rows, 'final_lock_rows': final_rows,
                               'final_read_error': final_read_error, 'local_mid_scalar_read_api': sorted(scalar_api),
                               'local_mid_scalar_api_verified_in': SCALAR_HEADER,
                               'native_headlamp_component_mutation_calls': False, 'direct_lit_writes': False,
                               'direct_apply_lock_calls': False, 'native_test_executed': bool(inputs),
                               'fresh_lobby_start': True, 'isolated_round3_initializer_fixture': True,
                               'natural_arrival_route_tested': False, 'full_round3_completion_tested': False,
                               'external_asset_saves_or_compiles': False,
                               'server_approach_teleport_and_controller_aim_fixtures': True,
                               'physical_F_key_or_gamepad_and_viewport_focus_tested': False,
                               'native_platform': ue.GameplayStatics.get_platform_name(),
                               'packet_emulation_tested': False, 'cross_platform_acceptance': False,
                               'readability_screenshots_or_shader_output_tested': False,
                               'optional_native_shot_showui': {'requested': capture_shots, 'shots': shots,
                                   'root_visual_review_completed': False, 'pixel_or_readability_acceptance': False,
                                   'captured_viewport_identity_verified': False},
                               'non_primary_host_owner_tested': any(item.get('non_primary_host_owner') for item in observations),
                               'failure_cleanup_leaves_headlamp_state_unrestored_if_native_input_failed': not bool(result['passed']),
                               'pose_restore_replication_settlement_awaited_on_success': bool(result['passed'])})
                persist(report_path, result)
                receipt.update({'status': 'passed' if result['passed'] else 'failed', 'stage': h.phase,
                                'finished_utc': utc(), 'error': error, 'cleanup_errors': result['cleanup_errors'],
                                'native_test_executed': bool(inputs), 'runtime_acceptance_pending': False,
                                'passed': bool(result['passed'])})
                persist(receipt_path, receipt)
            return result

        h.finish = finish
        cases = []
        state = {'case': 0, 'pulse': None, 'sample_at': 0., 'stable_since': None}

        def transition(name):
            h.transition(name)
            stage(name, {'case': state['case'], 'cases': len(cases)})

        def pulse(pid, requested, reason):
            assert state['pulse'] is None and (pid, 'lamp') not in h.controls, 'One F edge at a time'
            assert h.prop(h.locals[pid], 'view', 'bHeadlampOn') != requested, 'F edge must change the owner state exactly once'
            h.hold(pid, 'lamp')
            state['pulse'] = {'pid': pid, 'release_at': time.monotonic() + .18}
            inputs.append({'player_id': pid, 'action': support.ACTIONS['lamp'], 'key_binding': 'F',
                           'edge': 'press', 'requested_headlamp_on': requested, 'reason': reason,
                           'owner_world': h.locals[pid].get_world().get_path_name(), 'utc': utc()})

        def pulse_release():
            active = state['pulse']
            if active and time.monotonic() >= active['release_at']:
                h.release(active['pid'], 'lamp')
                inputs.append({'player_id': active['pid'], 'action': support.ACTIONS['lamp'],
                               'edge': 'release', 'utc': utc()})
                state['pulse'] = None

        def aim_native(pid, target):
            owner = h.locals[pid]
            eye, _rotation = owner.get_actor_eyes_view_point()
            destination = target.get_actor_location() + ue.Vector(0, 0, 35)
            owner.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(eye, destination))

        # RefreshBeam traces from the pawn's actual eye/base-aim rotation. Match
        # those APIs, while retaining the proven -110,+95 approach fixture.
        h.aim = aim_native

        def approach_case():
            pid, beam = cases[state['case']]
            cleanup_done.discard(pid)
            pos = beam.get_actor_location()
            h.fixture_place(pid, (pos.x - 110, pos.y, pos.z + 95))
            h.aims[pid] = beam
            h.aim(pid, beam)
            h.fixtures.append({'kind': 'maintained actual owning-controller aim fixture', 'player_id': pid,
                               'target': beam.get_name(), 'target_offset_cm': [0, 0, 35],
                               'eye_api': 'Pawn.get_actor_eyes_view_point', 'gameplay_light_state_written': False})
            transition('approach_beam')

        def unchanged_rows(rows):
            for row in rows:
                baseline = runtime_baseline[(row['world'], row['actor'])]
                # Root custom depth intentionally follows native Lit; it is not
                # compared. All recorded legacy geometry/collision is immutable.
                assert row['geometry'] == baseline['geometry'], ('Legacy root/collision/worldbounds changed', row, baseline)
                assert row['enabled'] == baseline['enabled'], 'Unexpected round/scaling mutation'
                # A detached MID can still report the right scalar, so keep
                # proving the rendered slot and imported visual stayed intact.
                for key in ('visual_mesh', 'visual_visible', 'visual_collision_enabled',
                            'visual_relative_location', 'visual_relative_scale',
                            'visual_absolute_scale', 'visual_materials', 'mid', 'mid_is_slot_1'):
                    assert row[key] == baseline[key], ('Imported local presentation changed', key, row, baseline)
                if not row['brazier']:
                    assert row['mid_is_slot_1'], ('Local Lit MID detached from visual slot 1', row)
                if row['brazier']:
                    assert row == baseline, ('Brazier changed during a headlamp-only test', row, baseline)

        def observe(expected):
            pid, beam = cases[state['case']]
            tool = h.comp(h.pawn(h.server, pid), 'tools')
            acquired = tool.get_editor_property('BeamTarget') == beam if expected else tool.get_editor_property('BeamTarget') is None
            rows = record_locks()
            unchanged_rows(rows)
            on_all_peers = all(h.prop(h.pawn(world, pid), 'view', 'bHeadlampOn') == expected for world in h.worlds)
            # Every other owner's lamp stays off, proving split-owner isolation.
            owner_isolation = all(not h.prop(h.pawn(world, other), 'view', 'bHeadlampOn') for world in h.worlds for other in h.ids if other != pid)
            targets = [row for row in rows if row['actor'] == beam.get_name()]
            matches = acquired and on_all_peers and owner_isolation and all(row['lit'] == expected and abs(row['mid_lit_scalar'] - (1. if expected else 0.)) <= .0001 for row in targets)
            # Sources are server-only bookkeeping. Remote SourceCount need not
            # replicate; do not infer replication from this unrelated field.
            server_row = next(row for row in targets if row['world'] == h.server.get_path_name())
            matches = matches and server_row['source_count'] == (1 if expected else 0)
            for row in rows:
                if not row['brazier'] and row['actor'] != beam.get_name():
                    assert not row['lit'] and abs(row['mid_lit_scalar']) <= .0001, ('Unrelated lock lit', row)
            return matches, {'gate': 'headlamp begin' if expected else 'headlamp end', 'owner': pid,
                             'target': beam.get_name(), 'rows': rows, 'server_beam_target_is_expected': acquired,
                             'owning_headlamp_state_on_all_peers': on_all_peers, 'other_owner_headlamps_unchanged': owner_isolation,
                             'non_primary_host_owner': h.locals[pid].get_world() == h.server and not h.locals[pid].get_controller().is_primary_player()}

        def capture_native_shot(pid, beam, expected, observation):
            if not capture_shots:
                return
            owner = h.locals[pid]
            controller = owner.get_controller()
            assert controller and controller.is_local_controller() and controller.get_world() == owner.get_world()
            folder = EVIDENCE / 'screenshots'
            folder.mkdir(parents=True, exist_ok=True)
            stamp = re.sub(r'[^A-Za-z0-9_-]', '', receipt['started_utc'])
            name = '-'.join((h.profile, str(h.n), stamp, 'owner' + str(pid), beam.get_name(), 'lit' if expected else 'unlit'))
            filename = folder / (name + '.png')
            # Installed GameViewportClient.cpp4284 recognizes SHOWUI, filename=
            # and -nosuffix. FScreenshotRequest is global in one-process PIE,
            # so the requested owner is recorded, not asserted as the captured
            # viewport. Root must inspect actual images before visual claims.
            command = 'Shot SHOWUI filename="' + str(filename) + '" -nosuffix'
            shots.append({'gate': observation['gate'], 'owner': pid, 'target': beam.get_name(),
                          'requested_owner_world': owner.get_world().get_path_name(),
                          'requested_controller': controller.get_path_name(), 'requested_file': str(filename),
                          'expected_lit_at_stable_request': expected, 'utc': utc(), 'command': command,
                          'scope': 'optional native qualitative preview; viewport/pixels not verified'})
            ue.SystemLibrary.execute_console_command(owner, command, controller)

        def tick(_delta):
            pulse_release()
            if h.phase == 'warmup':
                assert h.round()['phase'] == 0, 'Start this native gate in fresh Lobby'
                if h.elapsed() > 1:
                    before_round = h.round()
                    gm = ue.GameplayStatics.get_game_mode(h.server)
                    assert gm and ue.SystemLibrary.is_server(h.server)
                    stage('authorized_round3_initializer')
                    # Production StartRound only accepts Round 1 from Lobby,
                    # retry from Failed, or the next index from Cleared. Use its
                    # legal server chain, in this one callback, before Round 2
                    # director/taking timers tick. ClearRound(2) starts Round 3.
                    chain = []
                    for method, parameters, expected_index, expected_phase in (
                        ('StartRound', (1,), 1, 1),
                        ('ClearRound', (), 1, 2),
                        ('StartRound', (2,), 2, 1),
                        ('ClearRound', (), 3, 1),
                    ):
                        previous = h.round()
                        gm.call_method(method, args=parameters)
                        observed = h.round()
                        chain.append({'call': method, 'args': list(parameters),
                                      'before': previous, 'after': observed})
                        round_states.append({'stage': 'authorized fixture ' + method + str(parameters),
                                             'state': observed})
                        assert observed['index'] == expected_index and observed['phase'] == expected_phase, ('GameMode fixture chain rejected', chain)
                    after_round = h.round()
                    h.fixtures.append({'kind': 'parent-authorized isolated authoritative GameMode initializer',
                                       'call': 'StartRound(1) -> ClearRound() -> StartRound(2) -> ClearRound(); last call automatically starts3',
                                       'same_callback': True, 'calls': chain, 'world': h.server.get_path_name(),
                                       'round_before': before_round, 'round_after': after_round,
                                       'natural_arrival_route_proven': False, 'full_round3_completion_proven': False})
                    transition('await_round3_native_masks')
            elif h.phase == 'await_round3_native_masks':
                round_now = h.round()
                assert h.elapsed() < 8, ('Native Round 3 enabled masks did not settle', round_now)
                if h.elapsed() > 1 and round_now['index'] == 3 and round_now['phase'] == 1:
                    gs = ue.GameplayStatics.get_game_state(h.server)
                    scaling_row = str(gs.call_method('GetScalingRow'))
                    assert scaling_row == str(h.n), ('Unexpected native scaling row', scaling_row, h.n)
                    rows = record_locks()
                    peer_rounds = [round_for(world) for world in h.worlds]
                    def native_enabled(row):
                        count = (2 if scaling_row == '4' else 1) if row['brazier'] else (1 if scaling_row == '2' else 2)
                        return row['lock_slot'] < count
                    masks_ready = all(row['enabled'] == native_enabled(row) for row in rows)
                    masks_ready = masks_ready and all(row['index'] == 3 and row['phase'] == 1 for row in peer_rounds)
                    if masks_ready:
                        for row in rows:
                            validate_import(row)
                            assert not row['lit'] and row['source_count'] == 0
                            if not row['brazier']:
                                assert abs(row['mid_lit_scalar']) <= .0001
                            runtime_baseline[(row['world'], row['actor'])] = row
                        beams.extend(sorted([actor for actor in locks if not actor.get_editor_property('Brazier') and actor.get_editor_property('Enabled')], key=lambda actor: int(actor.get_editor_property('LockSlot'))))
                        assert beams, 'Native Round 3 has no enabled headlamp lock'
                        cases.extend((pid, beam) for pid in h.ids for beam in beams)
                        round_states.append({'stage': 'settled native Round 3 enabled masks', 'state': round_now,
                                             'peers': peer_rounds, 'scaling_row': scaling_row})
                        observations.append({'gate': 'Round 3 fixture initialized native enabled masks', 'rows': rows})
                        receipt.update({'enabled_native_headlamp_locks': [beam.get_name() for beam in beams],
                                        'case_roster': [{'player_id': pid, 'target': beam.get_name()} for pid, beam in cases],
                                        'round_state_observations': round_states})
                        approach_case()
            elif h.phase == 'approach_beam':
                assert h.round()['index'] == 3 and h.round()['phase'] == 1, 'Isolated native Round 3 changed during qualification'
                if h.elapsed() > 1:
                    pid, _beam = cases[state['case']]
                    pulse(pid, True, 'native owner headlamp begins beam')
                    state['stable_since'] = None
                    state['sample_at'] = 0.
                    transition('lamp_on')
            elif h.phase in ('lamp_on', 'lamp_off'):
                assert h.round()['index'] == 3 and h.round()['phase'] == 1, 'Isolated native Round 3 changed during qualification'
                if h.elapsed() > .4 and time.monotonic() >= state['sample_at']:
                    state['sample_at'] = time.monotonic() + .2
                    expected = h.phase == 'lamp_on'
                    matches, row = observe(expected)
                    state['last_observation'] = row
                    if matches:
                        if state['stable_since'] is None:
                            state['stable_since'] = time.monotonic()
                        if time.monotonic() - state['stable_since'] >= .4 and state['pulse'] is None:
                            observations.append(row)
                            capture_native_shot(row['owner'], cases[state['case']][1], expected, row)
                            h.checks.append({'name': 'Actual owning F lights local MID 1 on every peer' if expected else 'Actual owning F clears local MID to 0 on every peer', 'details': row})
                            if expected:
                                pid, _beam = cases[state['case']]
                                pulse(pid, False, 'native owner headlamp ends beam')
                                state['stable_since'] = None
                                transition('lamp_off')
                            else:
                                pid, _beam = cases[state['case']]
                                restore_owner(pid)
                                state['case'] += 1
                                if state['case'] < len(cases):
                                    approach_case()
                                else:
                                    h.aims.clear()
                                    cleanup_poses()
                                    transition('restored_pose_settle')
                    else:
                        state['stable_since'] = None
                    assert h.elapsed() < 8, ('Native F propagation did not satisfy peer Lit/MID/beam gate', row)
            elif h.phase == 'restored_pose_settle':
                assert h.round()['index'] == 3 and h.round()['phase'] == 1, 'Isolated native Round 3 changed during qualification'
                if h.elapsed() > 1:
                    rows = record_locks()
                    unchanged_rows(rows)
                    assert all(not row['lit'] and (row['brazier'] or abs(row['mid_lit_scalar']) <= .0001) for row in rows), rows
                    assert not h.controls and state['pulse'] is None and not h.aims
                    assert all(not h.prop(h.pawn(world, pid), 'view', 'bHeadlampOn') for world in h.worlds for pid in h.ids)
                    assert len(observations) == 2 + 2 * len(cases)
                    if h.profile == 'host_split':
                        assert any(item.get('non_primary_host_owner') for item in observations), 'Second non-primary host local owner was not qualified'
                    h.finish(True)

        receipt.update({'status': 'runtime_pending', 'runtime_acceptance_pending': True,
                        'optional_native_shot_showui_requested': capture_shots,
                        'authorized_initializer': 'server GameMode StartRound1 -> ClearRound1 -> StartRound2 -> ClearRound2 (auto starts3), once in one callback after fresh Lobby preflight',
                        'unchanged_native_braziers': [actor.get_name() for actor in braziers],
                        'case_roster': [{'player_id': pid, 'target': beam.get_name()} for pid, beam in cases]})
        stage('registered_native_tick_gate')
        result = h.register(tick)
        result.update({'startup_receipt': str(receipt_path), 'native_acceptance_not_yet_complete': True,
                       'required_observations': '2 per actual owner per natively enabled Round 3 headlamp lock',
                       'parent_only_execution': True})
        return result
    except BaseException as error:
        detail = traceback.format_exc()
        receipt.update({'status': 'startup_failed', 'finished_utc': utc(), 'error': str(error),
                        'exception_type': type(error).__name__, 'traceback': detail,
                        'native_test_executed': bool(inputs), 'runtime_acceptance_pending': False,
                        'passed': False})
        # If construction succeeded, release any already-held inputs and restore
        # fixtures through the Harness's registered cleanup; never save packages.
        if h is not None and not h.finished:
            try:
                h.finish(False, detail)
            except BaseException:
                receipt['cleanup_exception'] = traceback.format_exc()
        persist(receipt_path, receipt)
        failure_report = {}
        try:
            failure_report = json.loads(report_path.read_text())
        except Exception:
            pass
        failure_report.update({'passed': False, 'status': 'startup_failed', 'stage': receipt['stage'],
                               'error': str(error), 'traceback': detail, 'native_test_executed': bool(inputs),
                               'runtime_acceptance_pending': False, 'startup_receipt': str(receipt_path),
                               'profile': args.get('profile'), 'players': args.get('players')})
        persist(report_path, failure_report)
        print('HC-A4 native Lit prerequisite failed; receipt: ' + str(receipt_path))
        return {'queued': False, 'status': 'startup_failed', 'passed': False, 'error': str(error),
                'startup_receipt': str(receipt_path), 'report': str(report_path)}


RESULT = run(dict(globals().get('ARGS', {})))
