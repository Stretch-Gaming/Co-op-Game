import unreal as ue
sub=ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
mesh=ue.load_asset('/Game/Player/Art/Flares/SM_HandFlare')
RESULT={'simple':sub.get_simple_collision_count(mesh),'convex':sub.get_convex_collision_count(mesh),
        'options':ue.FbxStaticMeshImportData.__doc__,
        'decomposition_doc':sub.set_convex_decomposition_collisions.__doc__,
        'import_data':str(mesh.get_editor_property('asset_import_data'))}
