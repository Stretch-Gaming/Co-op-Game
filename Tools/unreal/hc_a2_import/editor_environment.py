"""Approved HZ environment support for #19. Run only in this isolated editor.

Creates unique assets and adds tagged actors; never replaces existing HZ actors.
No source art, shared material, gameplay, persistent map or project setting edits.
A held LFS lock and explicit --execute authoring request are required.
"""
import hashlib,json,math,subprocess
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-'),'Unreal 5.8.3 required'
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/'CoopGame.uproject'
request=json.loads((root/'Saved/HCA2/request.json').read_text(encoding='utf-8-sig'))
assert request.get('execute_environment') is True,'Explicit environment execution required'
locks=json.loads(subprocess.check_output(['git','lfs','locks','--json'],cwd=root,text=True))
assert any(x['path']=='Content/Hazards/L_Site01_HZ.umap' and x.get('owner',{}).get('name')=='StretchGaming' for x in locks),locks
if request.get('author_prototype_portal'):
 import runpy
 runpy.run_path(str(root/'Tools/unreal/hc_a2_import/editor_environment_portal.py'),run_name='__main__')
else:
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 assert levels.load_level('/Game/Maps/L_Site01')
 assert levels.set_current_level_by_name('L_Site01_HZ')
 assert levels.get_current_level().get_outermost().get_name()=='/Game/Hazards/L_Site01_HZ'
 dest='/Game/Hazards/Art/HCA2_Integration'
 mesh_path=dest+'/SM_HCA2_CaveSupport'
 if request.get('repair_owned_support') is True:
  evidence=json.loads((root/'Tools/unreal/hc_a2_import/evidence/environment_authoring.json').read_text())
  assert evidence['asset']==mesh_path
  binary=root/'Content/Hazards/Art/HCA2_Integration/SM_HCA2_CaveSupport.uasset'
  assert hashlib.sha256(binary.read_bytes()).hexdigest()==request['expected_support_sha256'],'Unexpected support asset change'
  for existing in actors.get_all_level_actors():
   if existing.actor_has_tag('HCA2_EnvironmentIntegration'):
    assert existing.get_outermost().get_name()=='/Game/Hazards/L_Site01_HZ'
    assert actors.destroy_actor(existing)
  existing=None
  assert unreal.EditorLoadingAndSavingUtils.save_packages([levels.get_current_level().get_outermost()],False)
  assert unreal.EditorAssetLibrary.delete_asset(mesh_path)
 assert not unreal.EditorAssetLibrary.does_asset_exist(mesh_path),'Refuse asset overwrite'
 assert not any(a.actor_has_tag('HCA2_EnvironmentIntegration') for a in actors.get_all_level_actors()),'Refuse repeat placement'
 def snapshot(a):
  p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
  return {'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':[p.x,p.y,p.z],'rotation':[r.pitch,r.yaw,r.roll],'scale':[s.x,s.y,s.z]}
 baseline={a.get_path_name():snapshot(a) for a in actors.get_all_level_actors()}
 boxes=[]
 def box(name,lo,hi,bevel=0):
  assert all(a<b for a,b in zip(lo,hi))
  boxes.append({'name':name,'min':list(lo),'max':list(hi),'bevel_cm':bevel})
 # Support floors have exact Z=0 walkable surfaces and overlapping seams.
 box('PassageFloor',(1450,-350,-100),(2550,350,0))
 box('HallFloor',(2450,-1750,-100),(5550,1950,0))
 box('TrapFloor',(5450,-350,-100),(8550,350,0))
 box('AltarFloor',(8450,-1400,-100),(11550,1400,0))
 box('G3Landing',(11450,-350,-100),(11850,350,0))
 box('HallSouth',(2500,-1750,-40),(5500,-1500,1050),35)
 for i,(lo,hi) in enumerate([(2500,3380),(3620,3880),(4120,4380),(4620,5500)]):
  box('HallNorth'+str(i),(lo,1500,-40),(hi,1750,1050),30)
 for x in (3500,4000,4500):
  box('AlcoveBack'+str(x),(x-140,1720,-30),(x+140,1970,1040),25)
  for direction in (-1,1):
   side=x+direction*120
   box('AlcoveReturn'+str(x)+'_'+str(direction),(side-30,1480,-30),(side+30,1970,1040),15)
 box('HallRoof',(2500,-1750,1000),(5500,1950,1250),40)
 box('AltarNorth',(8500,1200,-40),(11500,1450,1250),40)
 box('AltarSouth',(8500,-1450,-40),(11500,-1200,1250),40)
 box('AltarRoof',(8500,-1450,1200),(11500,1450,1450),40)
 box('AltarWestNorth',(8320,350,-30),(8680,1450,1250),25)
 box('AltarWestSouth',(8320,-1450,-30),(8680,-350,1250),25)
 box('AltarWestLintel',(8320,-350,400),(8680,350,1250))
 for name,start,end in [('Passage',1500,2500),('Trap',5500,8500)]:
  start+=180 if name=='Trap' else 0
  end-=180 if name=='Passage' else 0
  box(name+'North',(start,200,0),(end,450,400),20)
  box(name+'South',(start,-450,0),(end,-200,400),20)
  box(name+'Roof',(start,-450,400),(end,450,650),20)
 # Gate leaf slot is 34 cm thick on X. Full +400 cm travel ends at Z=850.
 # Flat pocket faces start at Z=400, occluding the rising leaf above the opening.
 for name,x,side in [('G1',2500,1750),('G2',5500,1750),('G3',11500,1450)]:
  for suffix,lo_x,hi_x in [('West',x-180,x-17),('East',x+17,x+180)]:
   box(name+'Pocket'+suffix,(lo_x,-350,512),(hi_x,350,900))
   # Below the frame top, keep padding behind its front/back lintel faces.
   inner_lo,inner_hi=(-33,-17) if suffix=='West' else (17,33)
   box(name+'PocketInner'+suffix,(x+inner_lo,-350,400),(x+inner_hi,350,512))
  top=1500 if name=='G3' else 1250
  box(name+'PocketCap',(x-180,-350,900),(x+180,350,top),20)
  box(name+'NorthCheek',(x-180,300,-40),(x+180,side,top))
  box(name+'SouthCheek',(x-180,-side,-40),(x+180,-300,top))
 # Close the already supported G3 landing, without extending the downstream scope.
 box('G3LandingNorth',(11680,200,-40),(11850,450,450),20)
 box('G3LandingSouth',(11680,-450,-40),(11850,-200,450),20)
 box('G3LandingRoof',(11680,-450,400),(11850,450,650),20)
 # Flat floor and precise pockets; chunky chamfered outer walls and roof.
 verts=[];normals=[];uvs=[];triangles=[]
 def face(points):
  base=len(verts);u=[points[1][i]-points[0][i] for i in range(3)];v=[points[2][i]-points[0][i] for i in range(3)]
  n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n));n=[x/length for x in n]
  verts.extend(points);normals.extend([n]*len(points));uvs.extend([[p[0]/500,p[1]/500] for p in points])
  for i in range(1,len(points)-1):triangles.append([base,base+i+1,base+i])
 for b in boxes:
  x0,y0,z0=b['min'];x1,y1,z1=b['max'];t=min(b['bevel_cm'],(x1-x0)/4,(y1-y0)/4,(z1-z0)/4)
  if not t:
   p=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
   for inds in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([p[i] for i in inds])
  else:
   def ring(inset,z):
    c=t if inset==0 else t/2
    return [(x0+inset+c,y0+inset,z),(x1-inset-c,y0+inset,z),(x1-inset,y0+inset+c,z),(x1-inset,y1-inset-c,z),(x1-inset-c,y1-inset,z),(x0+inset+c,y1-inset,z),(x0+inset,y1-inset-c,z),(x0+inset,y0+inset+c,z)]
   rings=[ring(t,z0),ring(0,z0+t),ring(0,z1-t),ring(t,z1)]
   face(list(reversed(rings[0])));face(rings[-1])
   for a,c in zip(rings,rings[1:]):
    for i in range(8):j=(i+1)%8;face([a[i],a[j],c[j],c[i]])
 dynamic=unreal.DynamicMesh();buffers=unreal.GeometryScriptSimpleMeshBuffers()
 buffers.vertices=[unreal.Vector(*v) for v in verts];buffers.normals=[unreal.Vector(*n) for n in normals]
 buffers.uv0=[unreal.Vector2D(*uv) for uv in uvs];buffers.triangles=[unreal.IntVector(*t) for t in triangles]
 unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buffers)
 opts=unreal.GeometryScriptCreateNewStaticMeshAssetOptions();opts.enable_nanite=len(triangles)>2000;opts.enable_collision=False
 mesh,outcome=unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,mesh_path,opts)
 assert mesh,(mesh_path,outcome)
 material=unreal.load_asset('/Game/Puzzles/Art/HCA2_Props/Materials/MI_HCA2_Stone');assert material
 mesh.set_material(0,material)
 body=mesh.get_editor_property('body_setup');agg=unreal.KAggregateGeom();elements=[]
 for b in boxes:
  lo,hi=b['min'],b['max'];e=unreal.KBoxElem();e.set_editor_property('name',b['name']);e.set_editor_property('center',unreal.Vector(*[(a+c)/2 for a,c in zip(lo,hi)]))
  for key,v in zip(('x','y','z'),[c-a for a,c in zip(lo,hi)]):e.set_editor_property(key,v)
  elements.append(e)
 agg.set_editor_property('box_elems',elements);body.set_editor_property('agg_geom',agg);body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
 settings=mesh.get_editor_property('nanite_settings');settings.set_editor_property('enabled',len(triangles)>2000);settings.set_editor_property('position_precision',4);settings.set_editor_property('fallback_percent_triangles',1.0);settings.set_editor_property('fallback_relative_error',0.0)
 unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_nanite_settings(mesh,settings,True)
 assert unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
 def tag(a,label):
  assert a.get_outermost().get_name()=='/Game/Hazards/L_Site01_HZ'
  a.set_actor_label(label);a.set_folder_path('HCA2_EnvironmentIntegration');a.set_editor_property('tags',[unreal.Name('HCA2_EnvironmentIntegration')])
 a=actors.spawn_actor_from_object(mesh,unreal.Vector(),unreal.Rotator(),False);tag(a,'HCA2_CaveSupport')
 a.static_mesh_component.set_collision_profile_name('BlockAll');a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
 lights=[]
 for label,loc,color,intensity,radius in [
  ('Plate_SW',(3100,-1050,300),(1,.4508,.063,1),35,1300),('Plate_NW',(3100,1000,300),(1,.4508,.063,1),35,1300),
  ('Plate_SE',(4700,-1050,300),(1,.4508,.063,1),35,1300),('Plate_NE',(4700,1000,300),(1,.4508,.063,1),35,1300),
  ('HallFill',(4000,0,650),(.0497,.6308,.5972,1),350,1900),
  ('Altar',(10650,-350,350),(1,.4508,.063,1),35,1400),('AltarFill',(10100,500,650),(.0497,.6308,.5972,1),350,1900),
  *[(name+'_West',(x-450,-100,300),(1,.4508,.063,1),30,1000) for name,x in [('G1',2500),('G2',5500),('G3',11500)]],
  *[(name+'_East',(x+(250 if name=='G3' else 450),100,300),(.0497,.6308,.5972,1),110,1000) for name,x in [('G1',2500),('G2',5500),('G3',11500)]],
  ('HallShadow_W',(3500,0,350),(.395,.548,1,1),160,1200),
  ('HallShadow_E',(4700,0,350),(.395,.548,1,1),160,1200),
  ('AltarShadow',(10700,0,400),(.395,.548,1,1),200,1300),
  *[(name+'_Shadow',(x-360,160,350),(.395,.548,1,1),100,1000) for name,x in [('G1',2500),('G2',5500),('G3',11500)]],
  *[('Trap_'+str(x),(x,0,300),(1,.4508,.063,1),80,1000) for x in (6300,7400,8200)]
 ]:
  a=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(*loc),unreal.Rotator(),False);tag(a,'HCA2_Light_'+label)
  c=a.get_component_by_class(unreal.PointLightComponent);c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',unreal.LightUnits.CANDELAS);c.set_intensity(intensity);c.set_attenuation_radius(radius);c.set_light_color(unreal.LinearColor(*color));c.set_editor_property('cast_shadows',True)
  lights.append({'label':label,'location':loc,'linear_color':color,'candela':intensity,'radius_cm':radius})
 a=None
 current={a.get_path_name():snapshot(a) for a in actors.get_all_level_actors()}
 assert all(current.get(k)==v for k,v in baseline.items()),'Unrelated actor changed'
 assert unreal.EditorLoadingAndSavingUtils.save_packages([levels.get_current_level().get_outermost()],False)
 report={'status':'authored; independent validation pending','authority':'Stretch explicitly approved HZ floor/lighting/gate-enclosure extension on 2026-10-10; #19 kickoff comment 6097208734','asset':mesh_path,'triangle_count':len(triangles),'nanite':len(triangles)>2000,'material':material.get_path_name(),'collision':'compound simple boxes; no complex-as-simple','boxes':boxes,'lights':lights,'preserved_existing_actors':len(baseline),'baseline':baseline,'source_license':'Team-authored analytic geometry through Unreal editor GeometryScripting API; public redistribution permitted, no external source or generated source art','saved_packages':[mesh_path,'/Game/Hazards/L_Site01_HZ']}
 (root/'Tools/unreal/hc_a2_import/evidence/environment_authoring.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('HCA2_ENVIRONMENT authored',len(boxes),len(triangles))
