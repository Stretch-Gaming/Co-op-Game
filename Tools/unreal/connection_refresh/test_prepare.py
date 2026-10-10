import gzip,json,pathlib,unittest
import prepare
class RefreshTests(unittest.TestCase):
 def test_baseline_selection_matches_existing_derivative(self):
  old=prepare.read_scene(prepare.ROOT/'SourceArt/HC/MazeIntegration/scene.json.gz');existing=prepare.read_scene(prepare.ROOT/'SourceArt/HC/EnvironmentConnection/connection.json.gz');draft=prepare.derivative(old)
  self.assertEqual([r['source_index']for r in draft['components']],[r['source_index']for r in existing['components']])
  self.assertEqual(draft['metadata']['clipped_record_indices'],existing['metadata']['clipped_record_indices'])
  self.assertEqual(draft['metadata']['excluded_non_environment_volumes'],[909])
 def test_latest_has_no_grading_cube_or_south_geometry(self):
  draft=prepare.read_scene(prepare.ROOT/'Saved/ConnectionRefresh/connection-draft.json.gz');self.assertEqual(draft['metadata']['excluded_non_environment_volumes'],[912]);self.assertEqual(len(draft['components']),563)
  for r in draft['components']:
   self.assertFalse(prepare.huge_query_box(r))
   if r['kind']=='procedural':
    self.assertTrue(all(v[1]+r['location'][1]>=prepare.CUT-1e-8 for v in r['vertices']))
    self.assertEqual(len(r['triangles'])%3,0);self.assertLess(max(r['triangles']),len(r['vertices']))
    for key in ['normals','uvs','vertex_colors']:self.assertEqual(len(r[key]),len(r['vertices']))
   elif r['kind']=='instanced':self.assertTrue(all(v['location'][1]>=prepare.CUT for v in r['instances']))
   else:self.assertGreaterEqual(r['location'][1],prepare.CUT)
 def test_triangle_clipping_interpolates_attributes(self):
  r={'name':'fixture','kind':'procedural','location':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1],'vertices':[[0,3100,0],[10,3300,0],[0,3300,0]],'normals':[[0,0,1]]*3,'uvs':[[0,0],[1,0],[0,1]],'vertex_colors':[[1,0,0,1],[0,1,0,1],[0,0,1,1]],'triangles':[0,1,2],'convex_hulls':[]}
  clipped,changed=prepare.clip_mesh(r);self.assertTrue(changed);self.assertEqual(len(clipped['triangles']),6);self.assertNotIn('convex_hulls',clipped)
  boundary=[(p,uv)for p,uv in zip(clipped['vertices'],clipped['uvs'])if p[1]==3200];self.assertTrue(any(uv==[.5,0]for p,uv in boundary));self.assertTrue(any(uv==[0,.5]for p,uv in boundary))
 def test_source_identity_and_determinism(self):
  raw=(prepare.ROOT/'Saved/ConnectionRefresh/pr122-scene.json.gz').read_bytes();self.assertEqual(prepare.digest(raw),prepare.NEW_OID);source=json.loads(gzip.decompress(raw));one=prepare.canonical(prepare.derivative(source));two=prepare.canonical(prepare.derivative(source));self.assertEqual(one,two)
  packed=gzip.compress(one,compresslevel=9,mtime=0);report=json.loads((prepare.ROOT/'Saved/ConnectionRefresh/audit.json').read_text());self.assertEqual(prepare.digest(packed),report['draft_sha256']);self.assertEqual(prepare.protected(),report['protected_sha256'])
if __name__=='__main__':unittest.main()
