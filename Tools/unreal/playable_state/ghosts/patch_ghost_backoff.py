"""Parent-only native pin splice: flare repulsion preserves longer backoff.

Only /Game/Player/Ghosts/BP_Ghost.RefreshFlareRepulsion may change. No graph
rebuild, target-guard change, phase/world change, or other asset save. Requires
the checkout containing this helper, stopped PIE, and a proven now + 0.2 source shape.
Run only in the root owner's serialized editor under the exact asset reservation.
"""
import json
import math
import traceback
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from Tools.unreal.playable_state.ghosts.context import ROOT, QUEUE
EXPECTED_PROJECT = ROOT
ASSET_PATH = '/Game/Player/Ghosts/BP_Ghost'
GRAPH_NAME = 'RefreshFlareRepulsion'
REPORT_PATH = QUEUE / 'ghost-backoff-patch-report.json'
RESULT = {
    'passed': False,
    'scope': {ASSET_PATH: [GRAPH_NAME]},
    'mutation_manifest': {
        'asset': ASSET_PATH,
        'graph': GRAPH_NAME,
        'new_nodes': ['GetBackoffUntil', 'Max(Float)'],
        'changed_existing_link': 'now + 0.2 -> SetBackoffUntil.BackoffUntil',
        'replacement': 'Max(GetBackoffUntil, original now + 0.2) -> same setter',
        'existing_nodes_deleted': [],
        'exec_links_changed': False,
        'other_graphs_changed': False,
        'save_only': ASSET_PATH,
    },
    'errors': [],
    'mutated': False,
    'save_attempted': False,
    'saved': False,
}
created = []
original_source = None
setter_input = None
bp = None
before = None
did_splice = False

try:
    import unreal as ue
    import toolset_registry
    from editor_toolset.toolsets.blueprint import BlueprintTools as BP

    def pin_key(pin):
        return (pin.get_owning_node().get_name(), str(pin.get_pin_name()))

    def physical_pin(node, name, direction):
        matches = [p for p in BP._list_pins(node, direction) if str(p.get_pin_name()) == name]
        assert len(matches) == 1, ('Expected one native pin', node.get_name(), name, len(matches))
        return matches[0]

    def info_pin(info, name, direction):
        pins = info.input_pins if direction == 'input' else info.output_pins
        matches = [p for p in pins if str(p.name) == name]
        assert len(matches) == 1, ('Expected one metadata pin', info.type_id, name)
        return matches[0]

    def is_number_type(value):
        # Exact native schema captured by the parent's live graph inventory.
        return str(value) == 'Float (double-precision)'

    def graph_snapshot(asset):
        result = {}
        for g in BP.list_graphs(asset):
            nodes = {}
            for node in BP.find_nodes(g):
                info = BP._get_node_info(node)
                pins = {}
                for direction, metadata, native_direction in (
                    ('input', info.input_pins, ue.EdGraphPinDirection.EGPD_INPUT),
                    ('output', info.output_pins, ue.EdGraphPinDirection.EGPD_OUTPUT),
                ):
                    metas = {str(p.name): p for p in metadata}
                    for p in BP._list_pins(node, native_direction):
                        name = str(p.get_pin_name())
                        meta = metas[name]
                        pins[direction + ':' + name] = {
                            'type': str(meta.type_id),
                            'default': str(getattr(meta, 'value', None)),
                            'links': sorted([list(pin_key(other)) for other in p.list_connected_pins()]),
                        }
                nodes[node.get_name()] = {'class': node.get_class().get_name(), 'type_id': str(info.type_id), 'pins': pins}
            result[g.get_name()] = nodes
        return result

    def deadline_add_source(pin):
        """Require numeric A+B, one literal0.2 and one direct game-time query."""
        node = pin.get_owning_node()
        info = BP._get_node_info(node)
        assert node.get_class().get_name() == 'K2Node_PromotableOperator'
        assert str(info.type_id) == 'Math|Float|float+float', ('Deadline source is not the inventoried addition', info.type_id)
        assert str(pin.get_pin_name()) == 'ReturnValue', ('Unexpected addition output', pin_key(pin))
        assert is_number_type(info_pin(info, 'ReturnValue', 'output').type_id), ('Non-numeric addition output', info.type_id)
        data_inputs = [p for p in info.input_pins if str(p.type_id).lower() != 'exec']
        assert {str(p.name) for p in data_inputs} == {'A', 'B'}, ('Unexpected addition inputs', str(info))
        assert all(is_number_type(p.type_id) for p in data_inputs), ('Non-numeric addition inputs', str(info))
        sources = {}
        for name in ('A', 'B'):
            p = physical_pin(node, name, ue.EdGraphPinDirection.EGPD_INPUT)
            links = list(p.list_connected_pins())
            assert len(links) == 1, ('Expected the inventoried direct addition source', name)
            source_node = links[0].get_owning_node()
            source_info = BP._get_node_info(source_node)
            assert source_node.get_class().get_name() == 'K2Node_CallFunction'
            assert str(links[0].get_pin_name()) == 'ReturnValue'
            assert is_number_type(info_pin(source_info, 'ReturnValue', 'output').type_id)
            if name == 'A':
                assert str(source_info.type_id) == 'Utilities|Time|GetGameTimeInSeconds', ('Deadline is not direct game time', source_info.type_id)
                sources['time_node'] = source_node.get_name()
            else:
                assert str(source_info.type_id) == 'Math|Float|MakeLiteralFloat', ('Deadline B is not the original float literal node', source_info.type_id)
                value_pin = physical_pin(source_node, 'Value', ue.EdGraphPinDirection.EGPD_INPUT)
                assert not list(value_pin.list_connected_pins()), 'Deadline literal Value must be unlinked'
                literal = info_pin(source_info, 'Value', 'input')
                assert is_number_type(literal.type_id)
                value = float(literal.value)
                assert math.isclose(value, 0.2, rel_tol=0, abs_tol=1e-6), ('Deadline constant is not0.2', value)
                sources['literal_node'] = source_node.get_name()
        return {'addition_node': node.get_name(), 'type_id': str(info.type_id), 'seconds': 0.2, **sources}

    actual_project = Path(ue.Paths.project_dir()).resolve()
    RESULT['project'] = str(actual_project)
    assert actual_project == EXPECTED_PROJECT.resolve(), ('Wrong editor project', str(actual_project))
    assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring'
    bp = ue.load_asset(ASSET_PATH)
    assert isinstance(bp, ue.Blueprint) and bp.get_path_name().split('.')[0] == ASSET_PATH
    assert 'BackoffUntil' in BP.list_variables(bp)
    graphs = {g.get_name(): g for g in BP.list_graphs(bp)}
    assert GRAPH_NAME in graphs
    graph = graphs[GRAPH_NAME]
    before = graph_snapshot(bp)
    RESULT['before'] = before
    RESULT['before_dsl'] = BP.read_graph_dsl(graph)
    nodes = list(BP.find_nodes(graph))
    setters = [n for n in nodes if str(BP._get_node_info(n).type_id).endswith('|SetBackoffUntil')]
    assert len(setters) == 1, ('Expected one BackoffUntil setter', len(setters))
    setter = setters[0]
    setter_info = BP._get_node_info(setter)
    assert setter.get_class().get_name() == 'K2Node_VariableSet'
    assert is_number_type(info_pin(setter_info, 'BackoffUntil', 'input').type_id)
    setter_input = physical_pin(setter, 'BackoffUntil', ue.EdGraphPinDirection.EGPD_INPUT)
    old_links = list(setter_input.list_connected_pins())
    assert len(old_links) == 1, 'Setter must have exactly one existing deadline source'
    original_source = old_links[0]

    # A safe second execution is a no-op, after validating the same exact shape.
    source_info = BP._get_node_info(original_source.get_owning_node())
    if str(source_info.type_id).endswith('|Max(Float)'):
        max_node = original_source.get_owning_node()
        max_a = physical_pin(max_node, 'A', ue.EdGraphPinDirection.EGPD_INPUT)
        max_b = physical_pin(max_node, 'B', ue.EdGraphPinDirection.EGPD_INPUT)
        a_links, b_links = list(max_a.list_connected_pins()), list(max_b.list_connected_pins())
        assert len(a_links) == len(b_links) == 1
        assert str(BP._get_node_info(a_links[0].get_owning_node()).type_id).endswith('|GetBackoffUntil')
        RESULT['preflight'] = deadline_add_source(b_links[0])
        RESULT.update({'passed': True, 'status': 'already_correct', 'after': before, 'after_dsl': RESULT['before_dsl']})
    else:
        RESULT['preflight'] = deadline_add_source(original_source)
        getter_types = [str(t) for t in BP.find_node_types(graph, 'GetBackoffUntil') if str(t).startswith('Variables|') and str(t).endswith('|GetBackoffUntil')]
        max_types = [str(t) for t in BP.find_node_types(graph, 'Max(Float)') if str(t).rsplit('|', 1)[-1] == 'Max(Float)']
        assert len(getter_types) == len(max_types) == 1, ('Ambiguous node catalog', getter_types, max_types)
        getter_type, max_type = getter_types[0], max_types[0]
        # Raw variable node type IDs are |GetBackoffUntil, while creation uses
        # the Variables|Default catalog ID. Validate by the exact variable leaf
        # and node class, using the existing headlamp graph as the prototype.
        assert 'RepelFromLight' in graphs
        prototype_nodes = list(BP.find_nodes(graphs['RepelFromLight']))
        prototypes = {}
        for label, leaf, node_class in (
            ('getter', 'GetBackoffUntil', 'K2Node_VariableGet'),
            ('max', 'Max(Float)', 'K2Node_CommutativeAssociativeBinaryOperator'),
        ):
            found = [n for n in prototype_nodes
                     if str(BP._get_node_info(n).type_id).rsplit('|', 1)[-1] == leaf
                     and n.get_class().get_name() == node_class]
            assert len(found) == 1, ('Expected one inventoried headlamp prototype before mutation', label, len(found))
            prototypes[label] = BP._get_node_info(found[0])
        assert is_number_type(info_pin(prototypes['getter'], 'BackoffUntil', 'output').type_id)
        for name in ('A', 'B'):
            assert is_number_type(info_pin(prototypes['max'], name, 'input').type_id)
        assert is_number_type(info_pin(prototypes['max'], 'ReturnValue', 'output').type_id)
        assert not any(str(p.type_id).lower() == 'exec' for p in [*prototypes['max'].input_pins, *prototypes['max'].output_pins])
        # Require exact matching schemas so the splice cannot add hidden
        # conversion/promotion nodes to any preexisting edge.
        numeric_types = {
            str(info_pin(setter_info, 'BackoffUntil', 'input').type_id),
            str(info_pin(BP._get_node_info(original_source.get_owning_node()), 'ReturnValue', 'output').type_id),
            str(info_pin(prototypes['getter'], 'BackoffUntil', 'output').type_id),
            str(info_pin(prototypes['max'], 'A', 'input').type_id),
            str(info_pin(prototypes['max'], 'B', 'input').type_id),
            str(info_pin(prototypes['max'], 'ReturnValue', 'output').type_id),
        }
        assert len(numeric_types) == 1, ('Mismatched numeric schemas; refuse implicit casts', sorted(numeric_types))
        RESULT['preflight'].update({'setter': setter.get_name(), 'original_source': list(pin_key(original_source)), 'getter_type': getter_type, 'max_type': max_type})

        # Mutation starts only after all preconditions and baseline audit pass.
        with toolset_registry.tool_raising_exceptions():
            getter = BP.create_node(graph, getter_type, ue.IntPoint(3000, -500), declaring_class=bp.generated_class())
            assert getter, 'Could not create BackoffUntil getter'
            created.append(getter)
            RESULT['mutated'] = True
            maximum = BP.create_node(graph, max_type, ue.IntPoint(3250, -500))
            assert maximum, 'Could not create numeric Max'
            created.append(maximum)
            getter_output = physical_pin(getter, 'BackoffUntil', ue.EdGraphPinDirection.EGPD_OUTPUT)
            maximum_a = physical_pin(maximum, 'A', ue.EdGraphPinDirection.EGPD_INPUT)
            maximum_b = physical_pin(maximum, 'B', ue.EdGraphPinDirection.EGPD_INPUT)
            maximum_output = physical_pin(maximum, 'ReturnValue', ue.EdGraphPinDirection.EGPD_OUTPUT)
            assert getter_output.try_create_connection(maximum_a)
            assert original_source.try_create_connection(maximum_b)
            setter_input.break_single_pin_link(original_source)
            did_splice = True
            assert maximum_output.try_create_connection(setter_input)

        after = graph_snapshot(bp)
        RESULT['after'] = after
        new_names = {n.get_name() for n in created}
        assert set(after) == set(before), 'Graph set changed'
        assert set(after[GRAPH_NAME]) == set(before[GRAPH_NAME]) | new_names, 'Unexpected created/deleted nodes'
        # Strip only the authorized old edge from baseline and the new-node
        # edges from the result. All original node types, defaults and links
        # (including every execution pin) must then match exactly.
        expected = json.loads(json.dumps(before))
        normalized_after = json.loads(json.dumps(after))
        old_source_key = pin_key(original_source)
        setter_key = pin_key(setter_input)
        for node_name, data in expected[GRAPH_NAME].items():
            for key, pin in data['pins'].items():
                name = key.split(':', 1)[1]
                if (node_name, name) == old_source_key:
                    pin['links'] = [link for link in pin['links'] if tuple(link) != setter_key]
                if (node_name, name) == setter_key:
                    pin['links'] = [link for link in pin['links'] if tuple(link) != old_source_key]
        for name in new_names:
            del normalized_after[GRAPH_NAME][name]
        for data in normalized_after[GRAPH_NAME].values():
            for pin in data['pins'].values():
                pin['links'] = [link for link in pin['links'] if link[0] not in new_names]
        assert normalized_after == expected, 'Unauthorized change to an original node/default/link or another graph'
        assert [pin_key(p) for p in setter_input.list_connected_pins()] == [pin_key(maximum_output)]
        assert [pin_key(p) for p in maximum_a.list_connected_pins()] == [pin_key(getter_output)]
        assert [pin_key(p) for p in maximum_b.list_connected_pins()] == [old_source_key]
        with toolset_registry.tool_raising_exceptions():
            BP.compile_blueprint(bp, warnings_as_errors=True)
        assert bp.get_editor_property('status') == ue.BlueprintStatus.BS_UP_TO_DATE
        assert graph_snapshot(bp) == after, 'Compile changed authored graph wiring; refuse save'
        RESULT['after_dsl'] = BP.read_graph_dsl(graph)
        RESULT['compile'] = 'passed; warnings as errors'
        RESULT['created_nodes'] = sorted(new_names)
        RESULT['save_attempted'] = True
        assert ue.EditorAssetLibrary.save_loaded_asset(bp, False), 'Ghost-only save failed'
        RESULT.update({'passed': True, 'status': 'patched', 'saved': True})
except Exception:
    RESULT['errors'].append(traceback.format_exc())
    # Restore the in-memory original wiring on any pre-save failure. Nothing
    # outside Ghost is touched; rollback is never followed by a Save All.
    if created and not RESULT['saved']:
        try:
            for node in reversed(created):
                BP.delete_node(node)
            if did_splice:
                assert original_source.try_create_connection(setter_input)
            assert graph_snapshot(bp) == before, 'Rollback differs from baseline'
            RESULT['rolled_back'] = True
            RESULT['rollback'] = graph_snapshot(bp)
        except Exception:
            RESULT['rolled_back'] = False
            RESULT['errors'].append('Rollback failed: ' + traceback.format_exc())
finally:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(RESULT, indent=2, default=str))
    RESULT['report'] = str(REPORT_PATH)
