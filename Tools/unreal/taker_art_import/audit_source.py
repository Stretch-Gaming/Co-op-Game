"""PG-A7 source audit. No Unreal/editor required; writes only this tooling folder."""
import hashlib, json, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from fbx_inspect import inspect_fbx
SRC=ROOT/'SourceArt/PG/PG-A7'
NAMES=('SM_Taker','SM_TakerArm')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    metrics=json.loads((SRC/'metrics.json').read_text())
    files=[]
    for p in sorted(SRC.rglob('*')):
        if p.is_file():
            assert not p.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'),str(p)
            files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    meshes={}
    for name in NAMES:
        a=inspect_fbx(SRC/(name+'.fbx'))
        assert a['all_triangles'] and a['triangles']==metrics[name]['triangles_exported']
        assert a['has_normals'] and a['uv_layer_count']==1
        assert a['global_settings']['UnitScaleFactor']==100 and a['global_settings']['UpAxis']==2
        a['manifold_pass']=a['boundary_edges']==a['non_manifold_edges']==a['loose_vertices']==0
        assert len(a['socket_models'])==len(metrics[name]['sockets_unreal_cm'])
        assert a['material_slots']==(['MI_Taker_Body','MI_Taker_Eyes'] if name=='SM_Taker' else ['MI_TakerArm_Body'])
        for raw,cm in zip(a['raw_vertex_dimensions'],metrics[name]['dimensions_cm']): assert abs(raw*100-cm)<.15
        meshes[name]=a
    textures={}
    for p in sorted((SRC/'textures').glob('*.png')):
        data=p.read_bytes(); assert data[:8]==b'\x89PNG\r\n\x1a\n'
        w,h,depth,color=struct.unpack('>IIBB',data[16:26]); assert (w,h)==(1024,1024)
        textures[p.name]={'width':w,'height':h,'bit_depth':depth,'color_type':color}
    report={'status':'source_warning_topology_editor_pending' if not all(m['manifold_pass'] for m in meshes.values()) else 'source_pass_editor_pending','source_pr':121,'source_commit':'60ae5e0250e790f943064f54e400574e8285463c','files':files,'meshes':meshes,'textures':textures,'author_report':metrics,
       'license':{'classification':'original team Blender modeling; no third-party assets or generator','public_redistribution':True,'attribution_required':False,'evidence':'SourceArt/PG/PG-A7/README.md final paragraph; PR121 body'},
       'pending':['UE scale/facing/pivot/socket validation','Unreal material/texture binding readback','dark cave/split-screen appearance','Mac fallback inspection','No gameplay or taking/chase integration performed']}
    (HERE/'source-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'files':len(files),'meshes':{n:meshes[n]['triangles'] for n in NAMES},'manifest_sha256':sha(HERE/'source-manifest.json')}))
if __name__=='__main__': main()
