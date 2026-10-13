"""Read-only Blueprint graph/pin snapshot; parent executes in its primary editor.

No graph edits, Blueprint compiles, asset saves, world changes, PIE lifecycle
calls, or gameplay function calls. Output is outside the repository. This only
records saved/current loaded graph wiring; it is not gameplay acceptance.
"""
import json
import traceback
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from Tools.unreal.playable_state.ghosts.context import ROOT, QUEUE
EXPECTED_PROJECT = ROOT
OUTPUT = QUEUE / 'ghost-target-pin-report.json'
RESULT = {
    'scope': 'read-only loaded Blueprint graph and pin connections',
    'runtime_acceptance': False,
    'asset_mutations': False,
    'assets': {},
    'errors': [],
}

try:
    import unreal as ue
    from editor_toolset.toolsets.blueprint import BlueprintTools as BP
    from editor_toolset.toolsets.data_table import DataTableTools as DT

    actual_project = Path(ue.Paths.project_dir()).resolve()
    RESULT['project'] = str(actual_project)
    assert actual_project == EXPECTED_PROJECT.resolve(), (
        'Wrong editor project; expected the checkout containing this helper', str(actual_project)
    )
    RESULT['engine'] = ue.SystemLibrary.get_engine_version()
    specs = {
        '/Game/Player/Ghosts/BP_Ghost': None,
        '/Game/Player/Ghosts/BP_GhostSpawner': None,
        '/Game/Player/Ghosts/BP_RoundGhostDirector': None,
        '/Game/Player/Ghosts/BP_ChaseDirector': None,
        '/Game/Player/Tools/AC_Tools': {
            'EventGraph', 'CanUseTools', 'GetFlareAllowance', 'RestockFlares',
            'ThrowFlareOnServer', 'RefreshBeam', 'ClearBeam', 'EndBeamTarget',
            'BeginTools', 'EndTools',
        },
        '/Game/Player/Tools/BP_Flare': {
            'EventGraph', 'IsActive', 'IsBurningFlare', 'RefreshFlare',
            'BeginFlare', 'EndFlare', 'EndFlareTarget', 'SetBurnSeconds',
        },
        '/Game/Player/AC_PlayerView': {
            'EventGraph', 'RepelFromLight', 'ApplyGhostLight', 'GhostInLight',
            'ChooseLightGhost', 'RefreshView', 'GetHeadlampOn',
        },
    }

    def link_record(pin):
        owner = pin.get_owning_node()
        return {'node': owner.get_name(), 'pin': str(pin.get_pin_name())}

    for asset_path, wanted in specs.items():
        asset_result = {'graphs': {}, 'errors': []}
        RESULT['assets'][asset_path] = asset_result
        try:
            bp = ue.load_asset(asset_path)
            if not isinstance(bp, ue.Blueprint):
                asset_result['missing'] = True
                continue
            asset_result['blueprint_status'] = str(bp.get_editor_property('status'))
            graphs = list(BP.list_graphs(bp))
            asset_result['available_graphs'] = [g.get_name() for g in graphs]
            for graph in graphs:
                name = graph.get_name()
                if wanted is not None and name not in wanted:
                    continue
                nodes = list(BP.find_nodes(graph))
                graph_result = {'node_count': len(nodes), 'nodes': [], 'errors': []}
                asset_result['graphs'][name] = graph_result
                assert len(nodes) <= 700, ('Bounded snapshot limit exceeded', asset_path, name, len(nodes))
                try:
                    graph_result['dsl'] = BP.read_graph_dsl(graph)
                except Exception:
                    graph_result['errors'].append('DSL read failed: ' + traceback.format_exc())
                for node in nodes:
                    node_result = {'name': node.get_name(), 'class': node.get_class().get_name(), 'pins': []}
                    graph_result['nodes'].append(node_result)
                    try:
                        info = BP._get_node_info(node)
                        node_result['type_id'] = str(info.type_id)
                        metadata = {
                            (label, str(p.name)): {
                                'native_type': str(p.type_id),
                                'default_value': getattr(p, 'value', None),
                            }
                            for label, pins in (('input', info.input_pins), ('output', info.output_pins))
                            for p in pins
                        }
                        for label, direction in (
                            ('input', ue.EdGraphPinDirection.EGPD_INPUT),
                            ('output', ue.EdGraphPinDirection.EGPD_OUTPUT),
                        ):
                            for pin in BP._list_pins(node, direction):
                                node_result['pins'].append({
                                    'name': str(pin.get_pin_name()),
                                    'direction': label,
                                    'links': [link_record(other) for other in pin.list_connected_pins()],
                                    **metadata.get((label, str(pin.get_pin_name())), {}),
                                })
                    except Exception:
                        node_result['error'] = traceback.format_exc()
        except Exception:
            asset_result['errors'].append(traceback.format_exc())

    RESULT['scaling_tables'] = {}
    for table_path in ('/Game/Player/DT_GhostScaling', '/Game/Hazards/DT_HazardScaling'):
        try:
            table = ue.load_asset(table_path)
            RESULT['scaling_tables'][table_path] = json.loads(DT.get_rows(table, ['2', '3', '4'])) if table else {'missing': True}
        except Exception:
            RESULT['scaling_tables'][table_path] = {'error': traceback.format_exc()}
    RESULT['completed'] = True
except Exception:
    RESULT['errors'].append(traceback.format_exc())
    RESULT['completed'] = False
finally:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(RESULT, indent=2, default=str))
    RESULT['report'] = str(OUTPUT)
