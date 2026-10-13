"""Read native HC-A4 receipts; missing evidence stays pending.

This tool does not import Unreal, execute authoring, edit asset binaries or turn
source previews into native acceptance. Completed runs need independent log proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ERRORS = re.compile(r'Blueprint Runtime Error|Accessed None|\bError:|\bFatal(?: error)?\b|Assertion failed', re.I)
PROFILE_CASES = (('joining', 2), ('host_split', 4))
EXPECTED_PACKAGES = {
    '/Game/Puzzles/Art/CrystalLock/SM_CrystalLock',
    '/Game/Puzzles/Art/CrystalLock/MI_CrystalLockStone',
    '/Game/Puzzles/Art/CrystalLock/M_CrystalLockCrystal',
    '/Game/Puzzles/BP_CrystalLock',
    '/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test',
}


def load(path):
    return json.loads(path.read_text()) if path.is_file() else None


def identity(path):
    return {'name': path.name, 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} if path.is_file() else None


def log_check(path, data):
    log = path.with_name(path.stem + '-log.txt')
    if not log.is_file():
        # Exact root driver log convention is lit-<profile>-<n>-log.txt.
        log = path.with_name(path.stem.removeprefix('crystal-lock-') + '-log.txt')
    counts = []
    result = {'receipt': identity(log), 'scanned_error_count': None, 'owner_reported_error_count': None}
    if log.is_file():
        errors = [line for line in log.read_text(errors='replace').splitlines() if ERRORS.search(line)]
        counts.append(len(errors))
        result.update(scanned_error_count=len(errors), error_excerpt=errors[:5])
    reported = data.get('native_log_errors')
    if isinstance(reported, list):
        reported = len(reported)
    if isinstance(reported, int) and not isinstance(reported, bool):
        counts.append(reported)
        result['owner_reported_error_count'] = reported
    result['clean'] = all(count == 0 for count in counts) if counts else None
    return result


def runtime_summary(path, expected_profile, expected_count):
    data = load(path)
    if data is None:
        return {'profile': expected_profile, 'players': expected_count, 'present': False, 'qualified': False}
    worlds = data.get('world_inventory', [])
    servers = [world for world in worlds if world.get('authoritative_game_mode')]
    clients = [world for world in worlds if not world.get('authoritative_game_mode')]
    owners = [pid for world in worlds for pid in world.get('local_player_ids', [])]
    host_count = sum(len(world.get('local_player_ids', [])) for world in servers)
    topology = (data.get('profile') == expected_profile and data.get('players') == expected_count
                and len(servers) == 1 and len(clients) == (expected_count if expected_profile == 'joining' else expected_count - 2)
                and host_count == (0 if expected_profile == 'joining' else 2)
                and len(owners) == len(set(owners)) == expected_count)
    observations = data.get('light_observations', [])
    edges = [item for item in observations if item.get('gate') in ('headlamp begin', 'headlamp end')]
    expected_locks = 1 if expected_count == 2 else 2
    expected_keys = {(pid, slot, edge) for pid in owners for slot in range(expected_locks) for edge in ('headlamp begin', 'headlamp end')}
    observed_keys = set()
    states_correct = True
    for edge in edges:
        target_rows = [row for row in edge.get('rows', []) if row.get('actor') == edge.get('target')]
        expected = edge['gate'] == 'headlamp begin'
        states_correct = states_correct and bool(target_rows) and len(target_rows) == len(worlds)
        states_correct = states_correct and all(row.get('lit') is expected and row.get('mid_is_slot_1') is True
            and abs(float(row.get('mid_lit_scalar', -99)) - int(expected)) <= .0001 for row in target_rows)
        states_correct = states_correct and edge.get('server_beam_target_is_expected') is True and edge.get('owning_headlamp_state_on_all_peers') is True
        states_correct = states_correct and edge.get('other_owner_headlamps_unchanged') is True
        if target_rows:
            observed_keys.add((edge.get('owner'), target_rows[0].get('lock_slot'), edge['gate']))
    input_owners = {edge.get('player_id') for edge in data.get('input_edges', []) if edge.get('edge') == 'press'}
    coverage = observed_keys == expected_keys and len(edges) == len(expected_keys) and input_owners == set(owners)
    log = log_check(path, data)
    scope = (data.get('fresh_lobby_start') is True and data.get('isolated_round3_initializer_fixture') is True
             and data.get('direct_lit_writes') is False and data.get('direct_apply_lock_calls') is False
             and data.get('native_headlamp_component_mutation_calls') is False and data.get('native_test_executed') is True)
    second_local = expected_profile != 'host_split' or data.get('non_primary_host_owner_tested') is True
    passed = data.get('passed') is True
    return {'receipt': identity(path), 'present': True, 'profile': expected_profile, 'players': expected_count,
            'passed': passed, 'topology_verified': topology, 'all_owners_and_enabled_locks_covered': coverage,
            'peer_lit_and_bound_mid_scalar_edges_verified': states_correct, 'second_host_local_verified': second_local,
            'isolated_fixture_and_owning_input_scope_verified': scope, 'cleanup_errors': data.get('cleanup_errors', []),
            'native_platform': data.get('native_platform'), 'native_log': log, 'error': data.get('error'),
            'qualified': passed and topology and coverage and states_correct and scope and second_local
                         and not data.get('cleanup_errors') and log['clean'] is True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, required=True)
    parser.add_argument('--project-root', type=Path, default=HERE.parents[3])
    parser.add_argument('--output', type=Path, default=HERE / 'evidence/summary.json')
    parser.add_argument('--complete', action='store_true')
    parser.add_argument('--repair-report', type=Path, help='Exact completed native map repair receipt, if import required repair')
    args = parser.parse_args()
    project = args.project_root.resolve()
    source_dir = project / 'SourceArt/HC/HC-A4'
    source_manifest = load(source_dir / 'source-manifest.json')
    assert source_manifest is not None, 'Delivered source manifest required'
    source_verified = all(identity(source_dir / name) is not None
        and identity(source_dir / name)['sha256'] == record['sha256'] for name, record in source_manifest['files'].items())
    receipt_path = args.raw_dir / 'unreal-fresh-import-receipt.json'
    imported = load(receipt_path)
    import_complete = bool(imported and imported.get('status') == 'succeeded'
                           and set(imported.get('saved_packages', [])) == EXPECTED_PACKAGES)
    result = imported.get('result', {}) if imported else {}
    import_verified = import_complete and result.get('source_fbx_sha256') == source_manifest['files']['SM_CrystalLock.fbx']['sha256']
    import_verified = import_verified and result.get('imported_slots') == ['M_CrystalLockStone', 'M_CrystalLockCrystal']
    import_verified = import_verified and result.get('simple_collision_hulls') == 1 and result.get('original_root_and_collision_preserved') is True
    import_verified = import_verified and len(result.get('mesh_dimensions_cm', [])) == 3 and all(abs(a-b) <= .1 for a,b in zip(result.get('mesh_dimensions_cm', []), [80,80,100]))
    repair_path = args.repair_report or args.raw_dir / 'placed-visual-repair-v2.json'
    if not repair_path.is_file() and args.repair_report is None:
        repair_path = args.raw_dir / 'placed-visual-repair.json'
    repair = load(repair_path)
    placed_verified = result.get('placed_headlamp_visual_mesh_and_collision_verified') is True
    placed_verified = placed_verified or bool(repair and repair.get('status') == 'passed'
        and repair.get('saved_packages') == ['/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test']
        and len(repair.get('changed', [])) == 2 and repair.get('blueprint_unchanged') is True
        and repair.get('root_collision_bounds_and_braziers_preserved') is True)
    runtime_dir = args.raw_dir / 'runtime-evidence'
    if not runtime_dir.is_dir():
        runtime_dir = args.raw_dir / 'runtime'  # Collected durable evidence layout.
    runs = [runtime_summary(runtime_dir / ('crystal-lock-lit-' + profile + '-' + str(count) + '.json'), profile, count)
            for profile, count in PROFILE_CASES]
    summary = {'schema': 1, 'purpose': 'HC-A4 headlamp crystal source, bounded native import and isolated Lit presentation',
               'source_manifest_verified': source_verified, 'source_metrics': load(source_dir / 'validation.json'),
               'native_import': {'receipt': identity(receipt_path), 'status': imported.get('status') if imported else 'pending',
                                 'stage': imported.get('stage') if imported else None,
                                 'saved_packages': imported.get('saved_packages', []) if imported else [],
                                 'complete_and_source_verified': bool(import_verified)},
               'placed_visual_binding': {'receipt': identity(repair_path),
                   'status': repair.get('status') if repair else 'pending',
                   'verified': placed_verified,
                   'saved_packages': repair.get('saved_packages', []) if repair else [],
                   'error': repair.get('error') if repair else None},
               'runtime_profiles': runs, 'collection_complete': bool(source_verified and import_verified and placed_verified and all(run['qualified'] for run in runs)),
               'full_mission_acceptance': False, 'natural_round3_arrival_route_tested': False,
               'windows_acceptance': False, 'physical_input_acceptance': False, 'native_rendered_15m_readability_acceptance': False,
               'historical_interruption': 'Host daemon restart during unsaved root continuation before SaveAll; original receipt retained as interrupted, not accepted.',
               'limits': ['Fresh Lobby -> authorized authoritative GameMode StartRound1/Clear1/StartRound2/Clear2 fixture chain in one callback; real placed locks and synthetic per-owner Enhanced Input F.',
                          'Server approach teleport and owning-controller aim fixtures; no direct Lit/ApplyLock/lightable/headlamp state writes.',
                          'Root geometry/collision, local MID slot binding and native braziers checked by runtime helper.',
                          'Source Blender previews do not establish native rendered or cross-platform readability.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + '\n')
    if args.complete and not summary['collection_complete']:
        raise SystemExit('Native import/runtime/log evidence remains incomplete; pending summary written')
    print(json.dumps({'summary': str(args.output), 'collection_complete': summary['collection_complete']}, indent=2))


if __name__ == '__main__':
    main()
