"""Prepare bounded collision probes from source geometry. No editor/network mutation."""
import collections,gzip,hashlib,json,pathlib
from math3d import position,normal,triangle,slope_degrees
ROOT=pathlib.Path(__file__).resolve().parents[3];SOURCE=ROOT/'SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/connection.json.gz';RAW=ROOT/'SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/scene.json.gz';OUTPUT=ROOT/'Saved/QualityGeometry'
def main(visible_only=False):
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()=='2008b7a684ba0f82d34b97fe259c20ec7abc46e09d00ead5f9c1dd8c6fcbf0ed';scene=json.loads(gzip.decompress(raw));original=json.loads(gzip.decompress(RAW.read_bytes()));cells={};hidden=[];triangles=0
 for r in scene['components']:
  if not r.get('collision'):continue
  if not r.get('visible',True):hidden.append({'label':'Connected_Maze_'+str(r['source_index']),'kind':r['kind'],'name':r['name'],'reason':'Invisible collision can be intentional support; requires native proof.'})
  if visible_only and not r.get('visible',True):continue
  if r['kind']!='procedural':continue
  vertices=[position(v,r)for v in r['vertices']];normals=[normal(v,r)for v in r['normals']]
  for start in range(0,len(r['triangles']),3):
   ids=r['triangles'][start:start+3];t=triangle(*(vertices[i]for i in ids));n=[sum(normals[k][j]for k in ids)/3 for j in range(3)];length=sum(x*x for x in n)**.5
   if not length or slope_degrees([x/length for x in n])>35 or t['area']<2000:continue
   p=t['centroid']
   if p[1]<4000:continue # Entry/fork already verified; do not repeat unchanged gate.
   triangles+=1;cell=(round(p[0]/500),round(p[1]/500),round(p[2]/100));candidate={'id':'floor_'+str(r['source_index'])+'_'+str(start//3),'point':p,'source_label':'Connected_Maze_'+str(r['source_index']),'triangle_area_cm2':t['area'],'source_slope_degrees':slope_degrees([x/length for x in n]),'reason':'Large upward collision triangle; proposed ground probe, not a path guarantee.','confidence':'source geometry only'}
   if cell not in cells or cells[cell]['triangle_area_cm2']<t['area']:cells[cell]=candidate
 ordered=sorted(cells.values(),key=lambda c:(c['point'][1],c['point'][0],c['point'][2]));count=min(64,len(ordered));selected=[ordered[round(i*(len(ordered)-1)/(count-1))]for i in range(count)]if count>1 else ordered
 stations=[]
 for s in original['stations']:
  if s['location'][1]<4000:continue
  p=list(s['location']);p[0]-=175;stations.append({'id':'station_'+s['name'],'point':p,'source_label':None,'reason':s['description'],'confidence':'authored landmark; mechanics may deliberately obstruct it'})
 movers=[{'name':m['name'],'rest':[m['rest'][0]-175,*m['rest'][1:]],'active':[m['active'][0]-175,*m['active'][1:]],'reason':'Deliberate lift/gate; do not remove or open for this audit.'}for m in original['movers']]
 pairs=[]
 for c in selected:
  near=sorted((sum((a-b)**2 for a,b in zip(c['point'][:2],d['point'][:2]))**.5,d['id'])for d in selected if d!=c and abs(d['point'][2]-c['point'][2])<45)
  if near and 0<near[0][0]<=750:
   pair=sorted([c['id'],near[0][1]])
   if pair not in pairs:pairs.append(pair)
 report={'selection_mode':'visible collision surfaces' if visible_only else 'all collision support surfaces','source_sha256':hashlib.sha256(raw).hexdigest(),'raw_sha256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'map':'/Game/Maps/L_ConnectedRoomMaze','sublevel':'/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze','large_floor_triangles':triangles,'candidate_cells':len(cells),'samples':selected+stations,'nearby_segment_pairs':pairs[:32],'deliberate_movers':movers,'invisible_collision_records':hidden,'native_collision_verified':False,'bugs_proven':[],'policy':'Source rays/sweeps are candidates only. Missing support or narrow/walled passages require design review; no geometry fixes generated.'}
 OUTPUT.mkdir(parents=True,exist_ok=True);(OUTPUT/'probe-plan.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k]for k in ['large_floor_triangles','candidate_cells','invisible_collision_records']}));print('bounded samples',len(report['samples']),'segments',len(report['nearby_segment_pairs']))
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--visible-surfaces',action='store_true');args=parser.parse_args();main(args.visible_surfaces)
