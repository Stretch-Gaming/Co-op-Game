import gzip,json,unreal as ue
from editor_toolset.toolsets.actor import ActorTools
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
sub='/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze'
if not ue.EditorAssetLibrary.does_asset_exist(sub):assert editor.new_level(sub);assert editor.save_current_level()
path='/Game/Maps/L_ConnectedRoomMaze'
if not ue.EditorAssetLibrary.does_asset_exist(path):assert editor.new_level(path)
else:assert editor.load_level(path)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',ue.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
for p in ('/Game/Hazards/L_Site01_HZ',sub):
 if not ue.GameplayStatics.get_streaming_level(world,p.rsplit('/',1)[-1]):assert ue.EditorLevelUtils.add_level_to_world(world,p,ue.LevelStreamingAlwaysLoaded)
assert editor.set_current_level_by_name('L_ConnectedRoomMaze')
if not [a for a in actors.get_all_level_actors()if isinstance(a,ue.PlayerStart) and a.get_level()==world.get_persistent_level()]:
 for i,x in enumerate((100,250,400,550)):
  a=actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(x,600,100),ue.Rotator(yaw=90));a.set_actor_label('Connected_Start_'+str(i))
assert ue.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
stream=ue.GameplayStatics.get_streaming_level(world,'L_ConnectedMaze');ue.EditorLevelUtils.make_level_current(stream)
scene=json.loads(gzip.decompress((ROOT/'SourceArt/HC/EnvironmentConnection/connection.json.gz').read_bytes()))
base='/Game/Puzzles/Art/MazeIntegration'
existing={a.get_actor_label()for a in actors.get_all_level_actors()if a.get_level()==stream.get_loaded_level()}
def transform(r):
 p,y,l=r['rotation'];return ue.Transform(location=ue.Vector(*r['location']),rotation=ue.Rotator(pitch=p,yaw=y,roll=l),scale=ue.Vector(*r['scale']))
def spawn(cls,label,r):
 tr=transform(r);a=actors.spawn_actor_from_class(cls,tr.translation,tr.rotation.rotator());assert a.get_level()==stream.get_loaded_level()
 a.set_actor_label(label);a.set_folder_path('Connected/Maze');a.set_editor_property('tags',[ue.Name('ConnectedEnvironment')]);a.set_actor_scale3d(tr.scale3d);return a
def mat(r):
 if r.get('material') and not r.get('tint'):return ue.load_asset(r['material'])
 tint=r.get('tint',r.get('color',[1,1,1,1]));suffix='_'.join(str(round(c*10000))for c in tint[:3])
 return ue.load_asset(base+'/Materials/MI_MazeTint_'+suffix+('_Style' if r.get('tint')else'_Flat')) or ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock')
count=0;instances=0
for r in scene['components']:
 i=r['source_index'];label='Connected_Maze_'+str(i)
 if label in existing:continue
 kind=r['kind']
 if kind=='point':
  a=spawn(ue.PointLight,label,r);c=a.get_component_by_class(ue.PointLightComponent);c.set_mobility(ue.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',ue.LightUnits.CANDELAS);c.set_editor_property('intensity',r['intensity']);c.set_editor_property('attenuation_radius',r['radius']);c.set_light_color(ue.LinearColor(*r['color']));c.set_editor_property('cast_shadows',r['shadow']);c.set_editor_property('max_draw_distance',5000.)
 elif kind=='instanced':
  a=spawn(ue.Actor,label,{'location':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1]});c=ActorTools.add_component(a,ue.HierarchicalInstancedStaticMeshComponent.static_class(),'MazeRocks');c.set_mobility(ue.ComponentMobility.STATIC);c.set_static_mesh(ue.load_asset(r['mesh']));c.set_material(0,mat(r));c.set_editor_property('cast_shadow',r['shadow']);c.set_collision_profile_name('BlockAll' if r['collision'] else 'NoCollision')
  for item in r['instances']:c.add_instance(transform(item),True)
  instances+=len(r['instances'])
 else:
  a=spawn(ue.StaticMeshActor,label,r);c=a.static_mesh_component;c.set_mobility(ue.ComponentMobility.STATIC)
  if kind=='procedural':
   mesh=ue.load_asset('/Game/Puzzles/EnvironmentConnection/Art/SM_Connection_'+str(i))if r.get('clipped')else ue.load_asset(base+f'/Meshes/SM_Maze_{i:04}')
   c.set_material(0,ue.load_asset(base+'/Materials/'+('M_MazeVertexGlow'if r.get('glow')else'M_MazeVertexLit')))
  elif kind=='blocker':mesh=ue.load_asset('/Engine/BasicShapes/Cube');a.set_actor_scale3d(ue.Vector(*(x/50 for x in r['extent'])));a.set_actor_hidden_in_game(True)
  else:mesh=ue.load_asset(r['mesh']);c.set_material(0,mat(r))
  assert mesh,(i,kind);c.set_static_mesh(mesh);c.set_collision_profile_name('BlockAll'if r.get('collision',kind=='blocker')else'NoCollision');c.set_editor_property('cast_shadow',r.get('shadow',False))
  if not r.get('visible',True):a.set_actor_hidden_in_game(True)
 count+=1
# A south wall closes the trimmed fork outside the existing 3 m north passage.
for label,x,width in [('Connected_Join_West',-1000,2350),('Connected_Join_East',1650,2350)]:
 if label in existing:continue
 a=spawn(ue.StaticMeshActor,label,{'location':[x,3200,300],'rotation':[0,0,0],'scale':[width/100,0.5,6]});a.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));a.static_mesh_component.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock'));a.static_mesh_component.set_collision_profile_name('BlockAll')
# The doorway is the sole route barrier; no puzzle actors or puzzle sublevels are loaded.
if 'Connected_Door' not in existing:
 a=actors.spawn_actor_from_class(ue.load_asset('/Game/Puzzles/EnvironmentConnection/BP_EnvironmentDoor').generated_class(),ue.Vector(325,1400,0),ue.Rotator())
 assert a.get_level()==stream.get_loaded_level();a.set_actor_label('Connected_Door');a.set_editor_property('tags',[ue.Name('ConnectedEnvironment'),ue.Name('ConnectionDoor')])
 origin,extent=a.get_actor_bounds(False);scale=ue.Vector(300/(extent.x*2),35/(extent.y*2),400/(extent.z*2));a.set_actor_scale3d(scale)
 origin,extent=a.get_actor_bounds(False);loc=a.get_actor_location();a.set_actor_location(loc+ue.Vector(325-origin.x,1400-origin.y,200-origin.z),False,True)
assert ue.EditorLoadingAndSavingUtils.save_packages([stream.get_loaded_level().get_outermost()],False)
RESULT={'map':path,'loaded_environment_levels':['/Game/Hazards/L_Site01_HZ',sub],'maze_actors_added':count,'instances_added':instances,'door':'Connected_Door','no_map_travel':True,'puzzle_levels_loaded':False}
(OUTPUT/'map-build.json').write_text(json.dumps(RESULT,indent=2))
