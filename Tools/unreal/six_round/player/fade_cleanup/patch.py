"""Guarded editor patch for ONE Blueprint; no taking/presentation builder import.

Run through the worktree/PID-specific private queue with ARGS.action inspect,
apply, audit, or save. A verified ownership receipt is mandatory for mutation.
Helper bodies are new graphs; existing graphs get only anchored node splices.
No save occurs until an explicit save request following native audit.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec
import importlib
importlib.reload(spec)


def guard():
    assert Path(ue.Paths.convert_relative_path_to_full(ue.Paths.project_dir())).resolve() == ROOT.resolve()
    assert int((QUEUE / 'pid').read_text()) == os.getpid()
    assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before graph work'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == spec.BASELINE
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'pg/pg6-taking-fade-cleanup'
    if ARGS['action'] in ('apply', 'save'):
        receipt = json.loads((QUEUE / 'mutation-guard.json').read_text())
        assert receipt['pid'] == os.getpid() and receipt['head'] == spec.BASELINE
        assert time.time() - receipt['epoch'] < 120, 'Refresh head/lock guard before mutation'
        assert receipt['lock']['path'] == spec.PACKAGE and receipt['lock']['id'] == '56118904'
        assert receipt['owned_lock_verified'] is True
    dirty = ue.EditorLoadingAndSavingUtils.get_dirty_content_packages() + ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert all(p.get_name() == spec.ASSET for p in dirty), [p.get_name() for p in dirty]


def nodes(graph):
    return list(BP.find_nodes(graph))


def pin_key(pin):
    return [pin.get_owning_node().get_name(), str(pin.get_pin_name())]


def snapshot(graph):
    result = []
    for node in nodes(graph):
        info = BP._get_node_info(node)
        pins = []
        for direction in (ue.EdGraphPinDirection.EGPD_INPUT, ue.EdGraphPinDirection.EGPD_OUTPUT):
            for pin in BP._list_pins(node, direction):
                pins.append({'name': str(pin.get_pin_name()), 'direction': str(direction),
                             'type': str(pin.get_pin_type_display_string()), 'value': pin.get_pin_value(),
                             'links': sorted(pin_key(p) for p in pin.list_connected_pins())})
        result.append({'name': node.get_name(), 'class': node.get_class().get_name(),
                       'type': info.type_id, 'pins': pins})
    return sorted(result, key=lambda n: n['name'])


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def inventory(bp):
    names = ue.BlueprintEditorLibrary.list_graph_names(bp)
    assert len(names) < 100, 'Refuse an unexpected graph inventory'
    return {str(name): snapshot(BP.get_graph(bp, str(name))) for name in names}


def exactly(items, description):
    assert len(items) == 1, (description, len(items))
    return items[0]


def entry(graph):
    return exactly([n for n in nodes(graph) if isinstance(n, ue.K2Node_FunctionEntry)], 'function entry')


def typed(graph, leaf):
    return [n for n in nodes(graph) if BP._get_node_info(n).type_id.rsplit('|', 1)[-1].lower() == leaf.lower()]


def anchor_preflight(bp):
    graphs = {name: BP.get_graph(bp, name) for name in spec.SPLICES}
    anchors = {}
    for name, graph in graphs.items():
        e = entry(graph); then = e.find_then_pin(); outgoing = list(then.list_connected_pins())
        assert len(outgoing) == 1, (name, 'entry continuation', len(outgoing))
        anchors[name] = (e, outgoing[0])
    visual = graphs['PlayTakingVisual']
    fade = exactly(typed(visual, 'SetManualCameraFade'), 'original manual fade')
    for name in ('self', 'InFadeAmount', 'Color', 'bInFadeAudio'):
        assert fade.find_input_pin(name), ('original fade pin', name)
    assert fade.find_input_pin('bInFadeAudio').get_pin_value().lower() == 'true'
    manager = exactly(list(fade.find_input_pin('self').list_connected_pins()), 'explicit camera manager').get_owning_node()
    assert BP._get_node_info(manager).type_id.rsplit('|', 1)[-1] == 'GetPlayerCameraManager'
    assert 'PlayerIndex' not in [str(p.get_pin_name()) for p in BP._list_pins(manager, ue.EdGraphPinDirection.EGPD_INPUT)], 'Refuse an indexed camera-manager lookup'
    controller = exactly(list(manager.find_input_pin('self').list_connected_pins()), 'camera controller')
    assert isinstance(controller.get_owning_node(), ue.K2Node_DynamicCast), 'Expected original controller cast'
    pawn = exactly([p for n in typed(visual, 'CastToPawn') for p in BP._list_pins(n, ue.EdGraphPinDirection.EGPD_OUTPUT)
                    if str(p.get_pin_name()).lower().startswith('as')], 'original victim pawn cast')
    assert len(fade.find_execute_pin().list_connected_pins()) == 1
    assert len(fade.find_input_pin('InFadeAmount').list_connected_pins()) == 1
    assert len(fade.find_input_pin('Color').list_connected_pins()) == 1
    # Verify the original authority path before any change; no original node is
    # rewritten or transplanted, including these replicated setters.
    finish = graphs['FinishTaking']
    unprotect = exactly(typed(finish, 'UnprotectVictim'), 'UnprotectVictim')
    victim = exactly([n for n in nodes(finish) if 'SetwithNotifyVictim' in BP._get_node_info(n).type_id], 'Victim notify setter')
    started = exactly([n for n in nodes(finish) if 'SetwithNotifyTakingStarted' in BP._get_node_info(n).type_id], 'schedule notify setter')
    assert pin_key(victim.find_execute_pin()) in [pin_key(p) for p in unprotect.find_then_pin().list_connected_pins()]
    assert pin_key(started.find_execute_pin()) in [pin_key(p) for p in victim.find_then_pin().list_connected_pins()]
    assert len([n for n in nodes(graphs['HideTakingPresentation']) if BP._get_node_info(n).type_id.endswith('|SetVisibility')]) == 5
    return graphs, anchors, fade, pawn, controller


def native_compile(bp):
    with toolset_registry.tool_raising_exceptions():
        BP.compile_blueprint(bp, warnings_as_errors=True)
    assert bp.get_editor_property('status') == ue.BlueprintStatus.BS_UP_TO_DATE


def new_graph(bp, name):
    definition = spec.HELPERS[name]
    graph = BP.add_function_graph(bp, name)
    for is_input, params in ((True, definition['inputs']), (False, definition['outputs'])):
        for param, kind in params:
            if kind in ('Pawn', 'PlayerController'):
                BP.add_object_function_param(graph, param, getattr(ue, kind).static_class(), is_input)
            else:
                BP.add_function_param(graph, param, kind, is_input)
    parameters = ' '.join(p for p, _ in definition['inputs'])
    code = f'(fn {name} ({parameters}) {definition["body"]})'
    blueprint_dsl.parse(code)
    palette_cache = {}
    def palette(query):
        if query not in palette_cache:
            palette_cache[query] = BP.find_node_types(graph, query)
        return palette_cache[query]
    def make(g, type_id, position):
        declaring = bp.generated_class() if type_id.startswith(('CallFunction|', 'Variables|')) else None
        if type_id.startswith('Class|PlayerController|'):
            declaring = ue.PlayerController.static_class()
        if not type_id.startswith('CallFunction|'):
            candidates = [str(t) for t in palette(type_id) if str(t).lower() == type_id.lower()]
            if not candidates:
                leaf = type_id.rsplit('|', 1)[-1].lower()
                candidates = [str(t) for t in palette(leaf) if str(t).rsplit('|', 1)[-1].lower() == leaf]
            if len(candidates) == 1:
                type_id = candidates[0]
        return BP.create_node(g, type_id, position, declaring_class=declaring)
    blueprint_dsl.Transpiler(graph, make, BP.connect_pins, BP._get_node_info, BP.set_pin_value,
        lambda g: BP.find_nodes(g), delete_node_fn=BP.delete_node, find_node_types_fn=palette).transpile(code)
    return graph


def splice(bp, name, graph, source, destination):
    call = BP.create_node(graph, 'CallFunction|' + spec.SPLICES[name], ue.IntPoint(-300, 0), declaring_class=bp.generated_class())
    source.find_then_pin().break_single_pin_link(destination)
    assert source.find_then_pin().try_create_connection(call.find_execute_pin())
    assert call.find_then_pin().try_create_connection(destination)


def copy_input(old, old_name, new, new_name):
    source = old.find_input_pin(old_name); target = new.find_input_pin(new_name)
    assert source and target, (old_name, new_name)
    connected = list(source.list_connected_pins())
    if connected:
        for pin in connected:
            assert pin.try_create_connection(target), (old_name, new_name)
    else:
        target.set_pin_value(source.get_pin_value())


def audit(bp, before, installed):
    current = inventory(bp)
    assert set(current) == set(before) | set(spec.HELPERS)
    changed_original = [name for name in before if current[name] != before[name]]
    assert set(changed_original) == set(spec.SPLICES), changed_original
    for name, helper in spec.SPLICES.items():
        graph = BP.get_graph(bp, name)
        call = exactly(typed(graph, helper), name + ' entry marker')
        assert pin_key(call.find_execute_pin()) in [pin_key(p) for p in entry(graph).find_then_pin().list_connected_pins()]
        assert BP._get_node_info(call).type_id.rsplit('|', 1)[-1] == helper
    assert not typed(BP.get_graph(bp, 'PlayTakingVisual'), 'SetManualCameraFade')
    replacement = exactly(typed(BP.get_graph(bp, 'PlayTakingVisual'), 'ApplyOwnedTakingFade'), 'replacement marker')
    assert BP._get_node_info(replacement).type_id.rsplit('|', 1)[-1] == 'ApplyOwnedTakingFade'
    assert all(BP.get_variable_replication(bp, name) == ue.BlueprintVariableReplication.NONE for name in spec.MEMBERS)
    assert len(typed(BP.get_graph(bp, 'ClearPresentedTakingFade'), 'SetManualCameraFade')) == 1
    assert len(typed(BP.get_graph(bp, 'ApplyOwnedTakingFade'), 'SetManualCameraFade')) == 1
    # Preserve every original node's type, position-independent pin contract and
    # defaults. Only the planned links and the single replaced fade node differ.
    for name, old_nodes in before.items():
        original = {n['name']: n for n in old_nodes}
        now = {n['name']: n for n in current[name]}
        removed = set(original) - set(now)
        expected_removed = {n['name'] for n in old_nodes if n['type'].endswith('|SetManualCameraFade')} if name == 'PlayTakingVisual' else set()
        assert removed == expected_removed, (name, 'removed original nodes', removed)
        for node_name in set(original) & set(now):
            a = {**original[node_name], 'pins': [{k: v for k, v in p.items() if k != 'links'} for p in original[node_name]['pins']]}
            b = {**now[node_name], 'pins': [{k: v for k, v in p.items() if k != 'links'} for p in now[node_name]['pins']]}
            assert a == b, (name, node_name, 'original node contract changed')
    for name in ('ClearPresentedTakingFade', 'ApplyOwnedTakingFade'):
        getter = exactly(typed(BP.get_graph(bp, name), 'GetPlayerCameraManager'), name + ' owning camera property')
        assert isinstance(getter, ue.K2Node_VariableGet)
        assert [str(p.get_pin_name()) for p in BP._list_pins(getter, ue.EdGraphPinDirection.EGPD_INPUT)] == ['self']
        assert 'Player Controller' in str(getter.find_input_pin('self').get_pin_type_display_string())
    cdo = BP.get_default_object(bp)
    for name, (_, default) in spec.MEMBERS.items():
        assert cdo.get_editor_property(name) == default, (name, 'cache default differs')
    if installed:
        assert current == installed, 'Installed graph/member contract differs; refuse repair/re-splice'
    return current


guard()
bp = ue.load_asset(spec.ASSET)
assert bp and bp.get_path_name().split('.')[0] == spec.ASSET
action = ARGS['action']
record = QUEUE / 'patch-before.json'; installed_record = QUEUE / 'patch-installed.json'
if action == 'inspect':
    anchor_preflight(bp)
    current = inventory(bp)
    RESULT = {'action': action, 'graphs': {k: current[k] for k in spec.SPLICES},
              'graph_hashes': {k: digest(v) for k, v in current.items()},
              'variables': list(BP.list_variables(bp)), 'status': str(bp.get_editor_property('status'))}
    record.write_text(json.dumps({'graphs': current, 'members': list(BP.list_variables(bp))}, indent=2))
elif action == 'apply':
    assert record.exists(), 'Inspect actual native anchors first'
    before = json.loads(record.read_text())
    present = set(BP.list_variables(bp)) & set(spec.MEMBERS)
    functions = set(map(str, ue.BlueprintEditorLibrary.list_graph_names(bp))) & set(spec.HELPERS)
    if present or functions:
        assert present == set(spec.MEMBERS) and functions == set(spec.HELPERS) and installed_record.exists(), 'Partial install; stop'
        audit(bp, before['graphs'], json.loads(installed_record.read_text())['graphs'])
        RESULT = {'action': action, 'unchanged': True, 'saved': False}
    else:
        assert inventory(bp) == before['graphs'], 'Native baseline changed since inspection'
        graphs, anchors, old, pawn, controller = anchor_preflight(bp)
        with ue.ScopedEditorTransaction('PG-6: owning taking fade cleanup (#93)'):
            bp.modify()
            for graph in graphs.values():
                graph.modify()
                for node in nodes(graph): node.modify()
            with toolset_registry.tool_raising_exceptions():
                for name, (kind, _) in spec.MEMBERS.items():
                    if kind in ('Pawn', 'PlayerController'): BP.add_object_variable(bp, name, getattr(ue, kind).static_class())
                    else: BP.add_variable(bp, name, kind)
                    BP.set_variable_instance_editable(bp, name, False)
                    BP.set_variable_replication(bp, name, ue.BlueprintVariableReplication.NONE)
                native_compile(bp)
                cdo = BP.get_default_object(bp)
                for name, (_, default) in spec.MEMBERS.items():
                    if default is not None: cdo.set_editor_property(name, default)
                for name in ('CanPresentTakingLocally', 'ClearPresentedTakingFade'): new_graph(bp, name)
                native_compile(bp)
                for name in ('ReconcilePresentedTakingFade', 'ApplyOwnedTakingFade'): new_graph(bp, name)
                native_compile(bp)
                for name, graph in graphs.items(): splice(bp, name, graph, *anchors[name])
                replacement = BP.create_node(graphs['PlayTakingVisual'], 'CallFunction|ApplyOwnedTakingFade', old.get_node_pos(), declaring_class=bp.generated_class())
                for pin in list(old.find_execute_pin().list_connected_pins()):
                    pin.break_single_pin_link(old.find_execute_pin()); assert pin.try_create_connection(replacement.find_execute_pin())
                for pin in list(old.find_then_pin().list_connected_pins()):
                    old.find_then_pin().break_single_pin_link(pin); assert replacement.find_then_pin().try_create_connection(pin)
                assert pawn.try_create_connection(replacement.find_input_pin('PresentedPawn'))
                assert controller.try_create_connection(replacement.find_input_pin('PresentedController'))
                for a, b in (('InFadeAmount', 'FadeAmount'), ('Color', 'FadeColor'), ('bInFadeAudio', 'FadeAudio')): copy_input(old, a, replacement, b)
                BP.delete_node(old)
                native_compile(bp)
                installed = audit(bp, before['graphs'], None)
                installed_record.write_text(json.dumps({'graphs': installed, 'members': list(spec.MEMBERS)}, indent=2))
        RESULT = {'action': action, 'unchanged': False, 'saved': False, 'original_changed_graphs': list(spec.SPLICES), 'new_helpers': list(spec.HELPERS), 'compile_warnings_as_errors': True}
elif action in ('audit', 'save'):
    assert record.exists() and installed_record.exists()
    before = json.loads(record.read_text()); installed = json.loads(installed_record.read_text())
    native_compile(bp)
    current = audit(bp, before['graphs'], installed['graphs'])
    readback = {name: BP.read_graph_dsl(BP.get_graph(bp, name)) for name in spec.HELPERS}
    for name, code in readback.items():
        assert 'GetPlayerController' not in code and 'GetPlayerPawn' not in code and 'SetViewTarget' not in code
        assert 'SetRoundState' not in code and 'SetTimer' not in code and 'SetwithNotifyVictim' not in code
    if action == 'save':
        assert ue.EditorAssetLibrary.save_loaded_asset(bp, False)
    RESULT = {'action': action, 'saved': action == 'save', 'compile_warnings_as_errors': True,
              'helper_readback': readback, 'graph_hashes': {k: digest(v) for k, v in current.items()}}
else:
    raise AssertionError(action)
(QUEUE / ('patch-' + action + '-result.json')).write_text(json.dumps(RESULT, indent=2))
