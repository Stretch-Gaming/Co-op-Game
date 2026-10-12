import unreal as ue
RESULT=[]
for path in ('/Game/Shared/Style/M_Stylized','/Game/Puzzles/EnvironmentConnection/Refresh_fd40cdeb/Materials/M_MazeVertexLit'):
    m=ue.load_asset(path);row={'path':path}
    for p in ('used_with_instanced_static_meshes','automatically_set_usage_in_editor'):
        try:row[p]=m.get_editor_property(p)
        except Exception as e:row[p]=str(e)
    RESULT.append(row)
