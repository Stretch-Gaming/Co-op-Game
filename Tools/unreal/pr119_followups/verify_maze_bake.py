"""Delete MI_MazeTint_* nothing references, then check L_Maze_HZ against the scene file."""
import collections, gzip, json
import unreal as ue
registry = ue.AssetRegistryHelpers.get_asset_registry()
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
scene = json.loads(gzip.decompress((ROOT / 'SourceArt/HC/MazeIntegration/scene.json.gz').read_bytes()))
pruned = []
for path in sorted(str(p).split('.')[0] for p in ue.EditorAssetLibrary.list_assets('/Game/Puzzles/Art/MazeIntegration/Materials', False, False)):
    if path.rsplit('/', 1)[-1].startswith('MI_MazeTint_') and not registry.get_referencers(path, ue.AssetRegistryDependencyOptions()):
        if ARGS.get('prune', False):
            assert ue.EditorAssetLibrary.delete_asset(path), path
        pruned.append(path.rsplit('/', 1)[-1])
placed = [a for a in actors.get_all_level_actors() if a.actor_has_tag('PlayableMazeScene')]
levels = collections.Counter(a.get_level().get_outermost().get_name() for a in placed)
labels = {a.get_actor_label() for a in placed}
missing = [i for i in range(len(scene['components'])) if 'MazeScene_%d' % i not in labels]
instances = sum(c.get_instance_count() for a in placed for c in a.get_components_by_class(ue.InstancedStaticMeshComponent))
no_mesh = [a.get_actor_label() for a in placed if isinstance(a, ue.StaticMeshActor) and not a.static_mesh_component.static_mesh]
RESULT = {'unreferenced_tints': pruned, 'pruned': ARGS.get('prune', False), 'placed': len(placed), 'levels': dict(levels), 'scene_components': len(scene['components']),
          'missing': missing[:20], 'instances': instances, 'scene_instances': sum(len(c.get('instances', [])) for c in scene['components']), 'static_mesh_actors_without_mesh': no_mesh[:20]}
