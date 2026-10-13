"""Parent-only read-only crystal SCS/CDO/editor/PIE inventory. Never compiles/saves.

Safe during PIE. GetObjectForBlueprint is only called for the owned non-inherited
HC_CrystalLockVisual; it can create inherited override templates, so those are
reported only via the read-only associated-object API.
"""
import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

PRIMARY = Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary').resolve()
BP_PATH = '/Game/Puzzles/BP_CrystalLock'
NAME = 'HC_CrystalLockVisual'
OUT = Path(globals().get('ARGS', {}).get('report', '/tmp/hc-a4-crystal-lock/crystal-visual-binding-inspection.json'))
assert OUT.resolve().is_relative_to(Path('/tmp').resolve())
assert Path(ue.Paths.project_dir()).resolve() == PRIMARY
REPORT = {'status': 'running', 'started_utc': datetime.now(timezone.utc).isoformat(),
          'project': str(PRIMARY), 'mutations': False, 'errors': []}

def persist():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix('.json.tmp');tmp.write_text(json.dumps(REPORT, indent=2) + '\n');tmp.replace(OUT)

def path(obj):
    return obj.get_path_name() if obj else None

def vec(value):
    return [float(value.x), float(value.y), float(value.z)]

def safe(fn):
    try:
        return fn()
    except Exception as error:
        return {'read_error': type(error).__name__ + ': ' + str(error)}

def component_row(component):
    if component is None:
        return None
    row = {'path': path(component), 'class': component.get_class().get_name(),
           'outer': path(component.get_outer()), 'package': component.get_outermost().get_name(),
           'owner': safe(lambda: path(component.get_owner()))}
    if isinstance(component, ue.SceneComponent):
        row.update({'relative_location': vec(component.get_editor_property('relative_location')),
                    'relative_scale': vec(component.get_editor_property('relative_scale3d')),
                    'relative_rotation': str(component.get_editor_property('relative_rotation')),
                    'absolute_scale': bool(component.get_editor_property('absolute_scale')),
                    'visible': bool(component.get_editor_property('visible')),
                    'attach_parent': safe(lambda: path(component.get_attach_parent())),
                    'mobility': str(component.get_editor_property('mobility'))})
    if isinstance(component, ue.StaticMeshComponent):
        row.update({'mesh': path(component.get_editor_property('static_mesh')),
                    'override_materials': [path(material) for material in component.get_editor_property('override_materials')],
                    'materials': [path(material) for material in component.get_materials()],
                    'collision_profile': str(component.get_collision_profile_name()),
                    'collision_enabled': str(component.get_collision_enabled()),
                    'configured_collision_enabled': str(component.get_editor_property('body_instance').get_editor_property('collision_enabled'))})
    return row

def actor_row(actor, kind):
    center, extent = actor.get_actor_bounds(False)
    return {'path': path(actor), 'name': actor.get_name(), 'kind': kind,
            'world': path(actor.get_world()), 'level': actor.get_level().get_outermost().get_name() if actor.get_level() else None,
            'Brazier': bool(actor.get_editor_property('Brazier')), 'Enabled': bool(actor.get_editor_property('Enabled')),
            'Lit': bool(actor.get_editor_property('Lit')), 'LockSlot': int(actor.get_editor_property('LockSlot')),
            'tags': [str(tag) for tag in actor.tags], 'location': vec(actor.get_actor_location()),
            'rotation': str(actor.get_actor_rotation()), 'scale': vec(actor.get_actor_scale3d()),
            'bounds_origin': vec(center), 'bounds_dimensions': [2*value for value in vec(extent)],
            'root': component_row(actor.static_mesh_component),
            'visual_property': safe(lambda: component_row(actor.get_editor_property(NAME))),
            'mid': safe(lambda: path(actor.get_editor_property('CrystalLockMID'))),
            'static_mesh_components': [component_row(component) for component in actor.get_components_by_class(ue.StaticMeshComponent)]}

persist()
try:
    bp = ue.load_asset(BP_PATH);assert bp
    REPORT['blueprint_status'] = str(bp.get_editor_property('status'))
    REPORT['generated_class'] = path(bp.generated_class())
    REPORT['graphs'] = {graph.get_name(): BP.read_graph_dsl(graph) for graph in BP.list_graphs(bp)}
    REPORT['graph_sha256'] = {name: hashlib.sha256(dsl.encode()).hexdigest() for name,dsl in REPORT['graphs'].items()}
    sds = ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
    lib = ue.SubobjectDataBlueprintFunctionLibrary
    scs_rows = []
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = lib.get_data(handle)
        name = str(lib.get_variable_name(data))
        inherited = bool(lib.is_inherited_component(data))
        row = {'variable': name, 'inherited': inherited, 'native': bool(lib.is_native_component(data)),
               'root_actor': bool(lib.is_root_actor(data)),
               'associated_object': component_row(lib.get_associated_object(data))}
        if name == NAME:
            assert not inherited and not row['native'], 'Refuse inherited/native template override creation'
            row['object_for_blueprint'] = component_row(lib.get_object_for_blueprint(data, bp))
        scs_rows.append(row)
    REPORT['subobjects'] = scs_rows
    # Reflection of SCS node storage is read-only and best-effort. The definitive
    # accessible binding is the freshly gathered owned subobject above.
    scs = safe(lambda: bp.get_editor_property('simple_construction_script'))
    if isinstance(scs, dict) or scs is None:
        REPORT['scs_reflection'] = scs
    else:
        REPORT['scs_reflection'] = {'path': path(scs)}
        nodes = safe(lambda: list(scs.get_editor_property('all_nodes')))
        if isinstance(nodes, dict):
            REPORT['scs_reflection']['all_nodes'] = nodes
        else:
            REPORT['scs_reflection']['all_nodes'] = [{'path': path(node),
                'variable': safe(lambda node=node: str(node.get_editor_property('internal_variable_name'))),
                'template': safe(lambda node=node: component_row(node.get_editor_property('component_template'))),
                'parent_component_or_variable_name': safe(lambda node=node: str(node.get_editor_property('parent_component_or_variable_name')))} for node in nodes]
    cdo = BP.get_default_object(bp)
    REPORT['cdo'] = {'path': path(cdo), 'root': component_row(cdo.static_mesh_component),
                     'visual_property': safe(lambda: component_row(cdo.get_editor_property(NAME))),
                     'components': [component_row(component) for component in cdo.get_components_by_class(ue.StaticMeshComponent)]}
    editor = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
    REPORT['editor_world'] = editor.get_outermost().get_name()
    REPORT['editor_actors'] = [actor_row(actor, 'editor') for actor in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors() if actor.get_class() == bp.generated_class()]
    REPORT['pie_worlds'] = []
    for world in ue.EditorLevelLibrary.get_pie_worlds(True):
        REPORT['pie_worlds'].append({'path': path(world), 'server': bool(ue.GameplayStatics.get_game_mode(world)),
            'dedicated_server': bool(ue.SystemLibrary.is_dedicated_server(world)),
            'actors': [actor_row(actor, 'PIE') for actor in ue.GameplayStatics.get_all_actors_of_class(world, bp.generated_class())]})
    REPORT.update(status='succeeded', finished_utc=datetime.now(timezone.utc).isoformat())
except BaseException as error:
    REPORT.update(status='failed', error=str(error), traceback=traceback.format_exc(), finished_utc=datetime.now(timezone.utc).isoformat())
    persist();raise
persist()
RESULT = {'report': str(OUT), 'status': REPORT['status'], 'subobjects': REPORT.get('subobjects'),
          'editor_visuals': [{'actor': row['name'], 'Brazier': row['Brazier'], 'components': row['static_mesh_components']} for row in REPORT.get('editor_actors', [])],
          'pie_world_count': len(REPORT.get('pie_worlds', []))}
