import pathlib,json,hashlib,subprocess
HERE=pathlib.Path(__file__).parent;ROOT=HERE.parents[2]
reports={n:json.loads((HERE/f'clients-{n}.json').read_text()) for n in [2,3,4]}
assert all(r['passed'] for r in reports.values())
assert not reports[4]['log_errors']
assert json.loads((HERE/'fresh-client-latejoin.json').read_text())['passed']
assert json.loads((HERE/'stale-key-rejection.json').read_text())['passed']
files=[ROOT/'Content/Puzzles/BP_Altar.uasset',*sorted((ROOT/'Content/Puzzles/Test/HC6_Altar').glob('*')),ROOT/'docs/hc6-altar-verification.md',*sorted(HERE.glob('*'))]
paths=[p for p in files if p.is_file() and p.name not in ['artifact-hashes.json','final-report.json']]
hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(HERE/'artifact-hashes.json').write_text(json.dumps(hashes,indent=2))
report={'scoped_altar_gate':'passed','native_client_counts':[2,3,4],'fresh_network_client':'passed','native_stale_key_rejection':'passed','client_authority':'passed','four_client_runtime_errors':reports[4]['log_errors'],'saved_interfaces':'BPI_Interactable/BPI_RoundReset','render':'altar-contact.png; contact reviewed, delivered cube key remains owner art handoff','blueprint_sha256':hashes['Content/Puzzles/BP_Altar.uasset'],'map_sha256':hashes['Content/Puzzles/Test/HC6_Altar/L_HC6_Altar.umap'],'baseline_unchanged_lfs_assets':695,'process_id':37752,'mcp_port':8042,'pie_port':17792,'pie_stopped':True,'temporary_settings_restored':True,'commits':0,'pending':['Primary independent review','Cave/trap placement and playtest','Core HC5 restart dispatcher','Stone-heart mesh/pivot owner integration','Physical gamepad and Mac/default-renderer tests','Unrelated AC_Carrying pending-kill Drop defect'],'unrun_optional_test':'test_split.py; not claimed'}
(HERE/'final-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
