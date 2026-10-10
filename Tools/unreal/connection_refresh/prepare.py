"""Offline PR122 review and deterministic HC environment derivative. Never imports unreal."""
import argparse, collections, copy, gzip, hashlib, json, math, pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]
REF='origin/pg/pr119-traps-maze'
NEW_OID='fd40cdeb47f2233c31125e16a2b62636734eb543ebd4f3ff4ae63a7ca6495b2a'
OLD_OID='7c738a4c7dddfd9723073f32bedea197927dbe7999c3c62f4a456e5868535fce'
CUT=3200.; SHIFT=-175.
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def read_scene(p):return json.loads(gzip.decompress(p.read_bytes()))
def protected():
 paths=['SourceArt/HC/MazeIntegration/scene.json.gz','SourceArt/HC/EnvironmentConnection/connection.json.gz','SourceArt/HC/EnvironmentConnection/provenance.json','Content/Maps/L_ConnectedRoomMaze.umap','Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap','Content/Puzzles/EnvironmentConnection/BP_EnvironmentDoor.uasset','Content/Hazards/L_Site01_HZ.umap']
 return {p:digest((ROOT/p).read_bytes())for p in paths}
def huge_query_box(r):return r['kind']=='blocker' and r['extent'][0]>5000 and r['extent'][1]>5000

def clip_mesh(r):
 # Exports bake mesh vertices in world axes. Refuse unsupported transforms.
 assert r['rotation']==[0,0,0] and r['scale']==[1,1,1],r['name']
 fields=['vertices','normals','uvs','vertex_colors']
 assert all(len(r[f])==len(r['vertices'])for f in fields)
 out={f:[] for f in fields};out['triangles']=[]
 localcut=CUT-r['location'][1]; all_above=all(v[1]>=localcut for v in r['vertices'])
 if all_above:return copy.deepcopy(r),False
 def interp(a,b):
  t=(localcut-a['vertices'][1])/(b['vertices'][1]-a['vertices'][1]);v={f:[x+(y-x)*t for x,y in zip(a[f],b[f])]for f in fields};v['vertices'][1]=localcut
  norm=math.sqrt(sum(x*x for x in v['normals']));v['normals']=[x/norm for x in v['normals']]if norm else [0,0,1]
  return v
 for start in range(0,len(r['triangles']),3):
  poly=[{f:r[f][i]for f in fields}for i in r['triangles'][start:start+3]]; result=[]
  prev=poly[-1];prev_in=prev['vertices'][1]>=localcut
  for cur in poly:
   cur_in=cur['vertices'][1]>=localcut
   if prev_in!=cur_in:result.append(interp(prev,cur))
   if cur_in:result.append(cur)
   prev,prev_in=cur,cur_in
  for n in range(1,len(result)-1):
   tri=[result[0],result[n],result[n+1]];a,b,c=[v['vertices']for v in tri];ab=[b[i]-a[i]for i in range(3)];ac=[c[i]-a[i]for i in range(3)]
   cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
   if sum(x*x for x in cross)<1e-16:continue
   index=len(out['vertices']);out['triangles'].extend([index,index+1,index+2])
   for v in tri:
    for f in fields:out[f].append(v[f])
 if not out['triangles']:return None,False
 record=copy.deepcopy(r);record.update(out);record.pop('convex_hulls',None);record['clipped']=True
 return record,True

def derivative(scene):
 records=[];excluded=[];clipped=[]
 for i,r in enumerate(scene['components']):
  if huge_query_box(r):excluded.append(i);continue
  if r['kind']=='procedural':
   rec,was_clipped=clip_mesh(r)
   if rec is None:continue
   if was_clipped:clipped.append(i)
  elif r['kind']=='instanced':
   rec=copy.deepcopy(r);rec['instances']=[copy.deepcopy(v)for v in r['instances']if v['location'][1]>=CUT]
   if not rec['instances']:continue
   # Existing assembly uses world-space instance transforms.
   for v in rec['instances']:v['location'][0]+=SHIFT
  else:
   if r['location'][1]<CUT:continue
   rec=copy.deepcopy(r)
  rec['source_index']=i;rec['location'][0]+=SHIFT
  records.append(rec)
 return {'components':records,'metadata':{'source_sha256':NEW_OID,'cut_world_y':CUT,'maze_offset_x':SHIFT,'purpose':'Environment only; no puzzle or trap activation','excluded_non_environment_volumes':excluded,'clipped_record_indices':clipped,'private_asset_base':'/Game/Puzzles/EnvironmentConnection/Refresh_fd40cdeb'}}

def audit(old,new,connection,changes):
 used={f'Content/Puzzles/Art/MazeIntegration/Meshes/SM_Maze_{r["source_index"]:04}.uasset' for r in connection['components']if r['kind']=='procedural' and not r.get('clipped')}
 touched=[{'status':status,'path':p}for status,p in changes if p in used]
 same=[];diff=[];removed=[]
 for i,r in enumerate(old['components']):
  if i>=len(new['components']):removed.append(i)
  elif canonical(r)==canonical(new['components'][i]):same.append(i)
  else:diff.append({'index':i,'old_kind':r['kind'],'new_kind':new['components'][i]['kind'],'old_name':r['name'],'new_name':new['components'][i]['name']})
 return {'old_components':len(old['components']),'new_components':len(new['components']),'new_kinds':dict(collections.Counter(r['kind']for r in new['components'])),'equal_at_same_index':same,'changed_at_same_index':diff,'old_indices_beyond_new_length':removed,'connected_shared_procedural_dependencies':len(used),'changed_connected_dependencies':touched,'deleted_shared_meshes':[p for status,p in changes if status=='D' and '/MazeIntegration/Meshes/'in p],'adoption_scope':'Private HC derivative only; do not merge HZ map/trap changes','protected_existing_paths_unchanged':True}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=pathlib.Path);args=ap.parse_args();out=ROOT/'Saved/ConnectionRefresh';out.mkdir(parents=True,exist_ok=True);before=protected()
 if args.source:source=args.source
 else:
  common=pathlib.Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip());source=common/'lfs/objects'/NEW_OID[:2]/NEW_OID[2:4]/NEW_OID
 raw=source.read_bytes();assert digest(raw)==NEW_OID,'PR122 source hash mismatch';(out/'pr122-scene.json.gz').write_bytes(raw)
 oldraw=(ROOT/'SourceArt/HC/MazeIntegration/scene.json.gz').read_bytes();assert digest(oldraw)==OLD_OID,'Old source changed; re-review required'
 old=json.loads(gzip.decompress(oldraw));new=json.loads(gzip.decompress(raw));connection=read_scene(ROOT/'SourceArt/HC/EnvironmentConnection/connection.json.gz')
 lines=subprocess.check_output(['git','diff','--name-status','e0bc313',REF],cwd=ROOT,text=True).splitlines();changes=[line.split('\t',1)for line in lines]
 draft=derivative(new);packed=gzip.compress(canonical(draft),compresslevel=9,mtime=0);(out/'connection-draft.json.gz').write_bytes(packed)
 report=audit(old,new,connection,changes);report.update({'source_ref':REF,'source_head':subprocess.check_output(['git','rev-parse',REF],cwd=ROOT,text=True).strip(),'source_sha256':NEW_OID,'draft_sha256':digest(packed),'draft_records':len(draft['components']),'draft_clipped_indices':draft['metadata']['clipped_record_indices'],'draft_excluded_volumes':draft['metadata']['excluded_non_environment_volumes'],'protected_sha256':before,'existing_paths_for_primary_only':['Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap','SourceArt/HC/EnvironmentConnection/connection.json.gz','SourceArt/HC/EnvironmentConnection/provenance.json'],'new_editor_asset_root':draft['metadata']['private_asset_base'],'runtime_verified':False})
 assert protected()==before,'Protected files changed during read-only preparation';(out/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k]for k in ['source_head','draft_records','draft_clipped_indices','draft_excluded_volumes','connected_shared_procedural_dependencies']}));print('changed_connected_dependencies',len(report['changed_connected_dependencies']))
if __name__=='__main__':main()
