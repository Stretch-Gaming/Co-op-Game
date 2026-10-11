"""Exact core runtime gate inventory and execution prerequisites; no game calls."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[5]
PACKET={
 'counts':[2,3,4],
 'sequential_callbacks':'Only one core test at a time. tests/stop.py explicitly stops/releases input without resetting game.',
 'compile_prerequisites':['Core round20 + resource_recovery + root escape_key_recovery','PG health/taking/cage/tools/chase/spectator and reliable owning RPC/input hooks','Test map/door/GameMode child + all reset interfaces','HUD native compile; no EnvironmentPreview or duplicated entrance'],
 'natural_round_setup':{'script':'core/test_map_native_flow.py','args':{'prepare_round':'1..6','runs':1},'behavior':'On a fresh Lobby, solve earlier puzzles through ordinary input and stop with all alive at the requested Playing round. Round2 waits until taking ends. Then invoke focused recovery/disconnect regression.'},
 'gates':[
  {'script':'core/test_map_native_gate.py','start':'Fresh test Lobby','counts':[2,3,4],'proves':'Each actual owning controller attempts E/movement; cannot bypass sole closed door'},
  {'script':'core/test_map_native_flow.py','args':{'runs':2,'timeout':240},'start':'Fresh test Lobby with a local listen host','counts':[2,3,4],'proves':'Two complete native puzzle transactions, feasible dead regroups, dead carrier drop/re-pick, exact-once altar score, delayed results/counts, owning results widgets and native host R return to second fresh run'},
  {'script':'core/test_map_native_flow.py','args':{'runs':1,'timeout':160},'start':'Dedicated PlayAsClient fresh Lobby','counts':[2,3,4],'proves':'Remote-owner puzzle/death/results scope; host R unavailable because dedicated server has no local host'},
  {'script':'core/test_wipe.py','args':{'case':'wipe'},'start':'Naturally reached Playing round1 through6; all alive, taking finished','counts':[2,3,4],'repeat_rounds':[1,2,3,4,5,6],'proves':'No direct round start/reset; dead input denial where survivors can continue; game failure countdown then exactly one attempt, all ColorSlot spots/full health/new-row flares; escape pedestal/cage-open'},
  {'script':'core/tests/run_impossible.py','start':'Naturally reached Playing round1/3/5 with all initially alive','counts':[2,3,4],'repeat_rounds':[1,3,5],'proves':'Game drives FailRound and three-second reset; 2-player R1 lost-statue and R3 exhausted-stock are explicitly resource fixtures, others use damage-only infeasible living counts'},
  {'script':'core/tests/run_lost_key.py','args':{'remove_key':False},'start':'Naturally reached Playing round6, alive roster','counts':[2,3,4],'proves':'Native Drop if carried, free relic placed below manifest lost height; game fails/retries with pedestal and cage open without player death'},
  {'script':'core/tests/run_lost_key.py','args':{'remove_key':True},'start':'Naturally reached Playing round6, alive roster','counts':[2,3,4],'proves':'Free relic destruction fixture; game must respawn cached pedestal key through failure/retry'},
  {'script':'core/tests/run_disconnect.py','start':'Naturally reached round4 with remote middle-slot client','counts':[3,4],'proves':'Actual local client disconnect, new-count retry, unchanged noncontiguous ColorSlots, matching active doors/checkpoint spots and new-row flare stock'}],
 'fixture_limits':['Approach teleportation and statue settling do not prove path traversal','Ghost separation during focused core transactions does not prove chase difficulty or presentation','Small relics near an interaction ray are temporarily moved/restored so they cannot disguise a focus regression','ApplyDamage/resource/property/removal/disconnect fixtures are test setup only; interaction/clear/failure/retry/pickup/delivery/restart functions are never called directly','2→1 disconnect needs an external rejoining client and is a separate live session gate; no fabricated local F5 eligibility during Failed'],
 'remaining_full_game_gates':['Every solo path walked with real movement/climb/sprint, not fixtures','Ghost/taking/chase visuals/audio/performance and actual trap exposure','Both split layouts plus physical gamepad and Mac clients','Fresh joining/leaving sessions including 2→1→2','Output Log AccessedNone/errors and independent saved asset/hash review'],
 'game_changes_for_primary':{'core/resource_recovery.py':'Only resource failure detection. No individual refund/spawn/restoration; FailRound owns three-second checkpoint recovery.','root/escape_key_recovery.py':'Root owns missing/lost relic recovery, not authored by this worker'},
 'acceptance':'Offline syntax only until primary executes gates; even passed fixture suites do not certify full mission traversal/presentation.'
}
if __name__=='__main__':
 out=ROOT/'Saved/SixRound/core-test-packet.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(PACKET,indent=2));print(json.dumps(PACKET,indent=2))
