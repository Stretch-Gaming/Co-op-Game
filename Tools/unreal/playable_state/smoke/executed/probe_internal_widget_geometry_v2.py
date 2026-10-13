"""Parent-only, one unsaved /Temp Blueprint diagnostic; NEVER save or Save All.

Action=build with stopped PIE: continue the SAME failed temporary Blueprint,
requiring the pinned original failed receipt and exactly its two terminators.
NO creation API is present; all graph mutations use public BlueprintTools. Four-node function: Widget input -> GetCachedGeometry ->
Slate GetLocalSize -> Vector2D output. Called on CDO; no component or actor added.
Action=measure in fresh 2-player PIE with one existing owning UI_Vehicle control:
compare internal Vector2D versus Python FGeometry roundtrip for the same objects,
including its nine descendants and both owners' actual HUD/prompt. No creation,
reattachment, inputs, gameplay, settings or asset changes during measure.

ARGS: action=build|measure, report_name='internal-widget-geometry-v2', and for
measure control_report_name='designer-control-runtime' (set to new control run).
Build receipt <report_name>-build.json; runtime receipt <report_name>-measure.json.
/Temp is dirty in-memory, not RF_Transient. Discard it at editor shutdown and
never call save APIs. A Vector2D divergence isolates the measurement boundary;
it does not alone prove HUD paint, root cause or a gameplay fix.
"""
import hashlib,json,math,os,re,time,traceback
from pathlib import Path
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

EXPECTED=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
SOURCE=Path('/tmp/coop-audit/probe_internal_widget_geometry_v2.py')
ARGS=globals().get('ARGS',{});ACTION=ARGS.get('action','build')
NAME=ARGS.get('report_name','internal-widget-geometry-v2')
assert ACTION in ('build','measure') and re.fullmatch(r'[A-Za-z0-9_-]+',NAME)
BASE=Path('/tmp/coop-audit/runtime-evidence')
BUILD=BASE/(NAME+'-build.json');OUT=BASE/(NAME+'-'+ACTION+'.json')
FUNCTION='ReadWidgetCachedLocalSize'
FAILED_RECEIPT=Path('/tmp/coop-audit/runtime-evidence/internal-widget-geometry-build.json')
FAILED_SHA='00d1656c152191fe0e1f160516a8574f7b9d72310d87eb18f49241554d0f41f2'
CACHED_ID='Widget|GetCachedGeometry'
SIZE_ID='UserInterface|Geometry|GetLocalSize'
PROTECTED=('VehicleTemplate/UI/UI_Vehicle','Puzzles/UI/HCA3/WBP_HCA3RoundHUD',
 'Puzzles/UI/WBP_InteractPrompt','Puzzles/UI/Results/WBP_RunResults',
 'Puzzles/UI/HCA3/AC_HCA3HUD','Core/BP_CoopCharacter')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(o):return o.get_path_name() if o else None
def vec(v):
 result=[float(v.x),float(v.y)]
 assert all(math.isfinite(x) for x in result),'Non-finite Vector2D result'
 return result
def positive(v):return all(x>1.0 for x in v)
def disk_hashes():return {p:sha(EXPECTED/'Content'/(p+'.uasset')) for p in PROTECTED}
def dirty():return sorted({p.get_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()}|{p.get_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()})
def write(r):
 BASE.mkdir(parents=True,exist_ok=True);temp=OUT.with_suffix('.json.tmp')
 temp.write_text(json.dumps(r,indent=2));temp.replace(OUT)
def info(n):return BP.get_node_infos([n])[0]
def pin(n,name,direction):
 i=info(n);pins=i.input_pins if direction=='input' else i.output_pins
 match=[p for p in pins if str(p.name)==name]
 assert len(match)==1,(ref(n),name,direction,[str(p.name) for p in pins])
 return match[0].pin_id
def exec_pins(n,direction):
 i=info(n);pins=i.input_pins if direction=='input' else i.output_pins
 return [p.pin_id for p in pins if str(p.type_id).lower()=='exec']
def exact_type(graph,type_id):
 matches=[str(x) for x in BP.find_node_types(graph,type_id) if str(x)==type_id]
 assert matches==[type_id],('Exact UMG catalog entry unavailable',type_id,matches)
 return type_id
def meta_pin(n,name,direction):
 i=info(n);pins=i.input_pins if direction=='input' else i.output_pins
 matches=[p for p in pins if str(p.name)==name];assert len(matches)==1
 return matches[0]
def same_pin(a,b):return a.node==b.node and a.index_id==b.index_id and a.direction==b.direction
def node_manifest(graph):
 return [{'node':ref(i.node),'class':i.node.get_class().get_name(),'type_id':str(i.type_id),
  'inputs':[{'name':str(p.name),'type':str(p.type_id),'connections':len(p.connected_pins)} for p in i.input_pins],
  'outputs':[{'name':str(p.name),'type':str(p.type_id),'connections':len(p.connected_pins)} for p in i.output_pins]}
  for i in BP.get_node_infos(BP.find_nodes(graph))]

R={'schema':1,'action':ACTION,'passed':False,'collection_complete':False,'packages_saved':[],
 'editor_pid':os.getpid(),'script_file':str(SOURCE),'script_sha256':sha(SOURCE),
 'rendered_pixel_acceptance':False,'native_log_scan_pending':True,
 'scope':'one unsaved /Temp ActorComponent Blueprint; CDO only; no actors/component attachment/HUD/template/settings edits'}
probe=None
try:
 assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
 assert not OUT.exists(),'Distinct report_name required; no historical receipt overwrite'
 original=disk_hashes();R['protected_disk_hashes_before']=original
 if ACTION=='build':
  assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE before compiling temporary diagnostic'
  R['dirty_packages_before']=dirty()
  assert sha(FAILED_RECEIPT)==FAILED_SHA,'Original failure receipt changed'
  failed=json.loads(FAILED_RECEIPT.read_text())
  assert failed['editor_pid']==os.getpid() and not failed['passed'] and failed['saved_bytes_preserved']
  assert failed['packages_saved']==[] and failed['script_sha256']=='cd9619d41279d64983fed8b1c979120f20be6e20951429f80e1d577930acd4bf'
  assert original==failed['protected_disk_hashes_before']==failed['protected_disk_hashes_after']
  package=failed['package']
  assert package=='/Temp/CoopAudit/BP_InternalGeometry_81093_1f13b18378','Unexpected original temporary package'
  R['package']=package;R['not_rf_transient']=True;R['package_must_be_discarded_without_save']=True
  R['continuation_of_failed_receipt']=str(FAILED_RECEIPT);R['failed_receipt_sha256']=FAILED_SHA
  R['creation_apis_called']=0;write(R)
  with toolset_registry.tool_raising_exceptions():
   bp=ue.load_object(None,package+'.'+package.rsplit('/',1)[-1])
   assert bp and isinstance(bp,ue.Blueprint) and bp.get_path_name().split('.')[0]==package and bp.get_outer().get_name()==package
   assert bp.get_editor_property('ParentClass')==ue.ActorComponent.static_class()
   graphs=[g for g in BP.list_graphs(bp) if g.get_name()==FUNCTION];assert len(graphs)==1
   graph=graphs[0];nodes=BP.find_nodes(graph)
   entry=[n for n in nodes if n.get_class().get_name()=='K2Node_FunctionEntry']
   result=[n for n in nodes if n.get_class().get_name()=='K2Node_FunctionResult']
   assert len(entry)==len(result)==1 and len(nodes)==2,'Continuation requires exact original two-terminator graph'
   widget_meta=meta_pin(entry[0],'WidgetTarget','output');output_meta=meta_pin(result[0],'LocalSize','input')
   assert not widget_meta.connected_pins and not output_meta.connected_pins,'Original measurement data pins must be unwired'
   normalize_type=lambda t:re.sub(r'[^a-z0-9]','',str(t).lower())
   assert normalize_type(widget_meta.type_id)=='widgetobjectreference' and normalize_type(output_meta.type_id)=='vector2dstructure',('Unexpected parameter types',str(widget_meta.type_id),str(output_meta.type_id))
   widget_pin=widget_meta.pin_id;output_pin=output_meta.pin_id
   entry_exec=exec_pins(entry[0],'output');result_exec=exec_pins(result[0],'input')
   assert len(entry_exec)==len(result_exec)==1
   entry_connections=[p for p in info(entry[0]).output_pins if str(p.type_id).lower()=='exec'][0].connected_pins
   result_connections=[p for p in info(result[0]).input_pins if str(p.type_id).lower()=='exec'][0].connected_pins
   assert len(entry_connections)==len(result_connections)<=1
   if entry_connections:assert same_pin(entry_connections[0],result_exec[0]) and same_pin(result_connections[0],entry_exec[0]),'Unexpected preexisting execution link'
   R['initial_two_terminators']=node_manifest(graph)
   cached_type=exact_type(graph,CACHED_ID);size_type=exact_type(graph,SIZE_ID)
   cached=BP.create_node(graph,cached_type,ue.IntPoint(250,100),ue.Widget.static_class())
   slate=ue.load_class(None,'/Script/UMG.SlateBlueprintLibrary');assert slate
   size=BP.create_node(graph,size_type,ue.IntPoint(500,100),slate)
   BP.connect_pins(widget_pin,pin(cached,'self','input'))
   BP.connect_pins(pin(cached,'ReturnValue','output'),pin(size,'Geometry','input'))
   BP.connect_pins(pin(size,'ReturnValue','output'),output_pin)
   assert not exec_pins(cached,'input') and not exec_pins(cached,'output'),'Expected const cached-geometry getter to be pure'
   assert not exec_pins(size,'input') and not exec_pins(size,'output'),'Expected Slate size getter to be pure'
   if not entry_connections:BP.connect_pins(entry_exec[0],result_exec[0])
   assert len(BP.find_nodes(graph))==4,'Temporary measurement graph must contain exactly four nodes'
   BP.compile_blueprint(bp,warnings_as_errors=True)
   cdo=BP.get_default_object(bp);assert cdo and cdo.get_class()==bp.generated_class()
  R.update({'blueprint_path':ref(bp),'generated_class':ref(bp.generated_class()),'cdo':ref(cdo),
   'function':FUNCTION,'graph_dsl':BP.read_graph_dsl(graph),'graph_nodes':node_manifest(graph),
   'compile_status':str(bp.get_editor_property('Status')),'actor_or_component_instances_created':0,
   'dirty_packages_after':dirty(),'collection_complete':True})
  R['unexpected_new_dirty_packages']=sorted(set(R['dirty_packages_after'])-set(R['dirty_packages_before'])-{package})
  assert not R['unexpected_new_dirty_packages'],'A package outside the exact /Temp diagnostic became dirty'
  assert disk_hashes()==original,'Protected saved bytes changed'
  R.update({'protected_disk_hashes_after':disk_hashes(),'saved_bytes_preserved':True,'passed':True,'status':'compiled_unsaved_temp_cdo_ready'})
  write(R)
 else:
  receipt=json.loads(BUILD.read_text());assert receipt['passed'] and receipt['editor_pid']==os.getpid()
  assert receipt['script_sha256']==sha(SOURCE) and receipt['function']==FUNCTION
  assert receipt['blueprint_path'].startswith('/Temp/CoopAudit/BP_InternalGeometry_')
  assert original==receipt['protected_disk_hashes_before'],'Protected source snapshot changed since build'
  bp=ue.load_object(None,receipt['blueprint_path']);assert bp and isinstance(bp,ue.Blueprint)
  cdo=BP.get_default_object(bp);assert ref(cdo)==receipt['cdo'] and ref(cdo.get_class())==receipt['generated_class']
  control_name=ARGS.get('control_report_name','designer-control-runtime');assert re.fullmatch(r'[A-Za-z0-9_-]+',control_name)
  control_receipt=json.loads((BASE/(control_name+'.json')).read_text())
  assert control_receipt['editor_pid']==os.getpid() and control_receipt['collection_complete'] and control_receipt['control_left_attached']
  controls=[w for w in ue.ObjectIterator(ue.UserWidget) if ref(w)==control_receipt['control_path']]
  assert len(controls)==1;control=controls[0];pc=control.get_owning_player()
  assert pc and pc.is_local_controller() and ref(pc)==control_receipt['owner_controller'] and control.is_in_viewport()
  assert ref(control.get_class())=='/Game/VehicleTemplate/UI/UI_Vehicle.UI_Vehicle_C'
  assert ue.get_engine_subsystem(ue.GameViewportSubsystem).is_widget_added(control)
  worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert 2<=len(worlds)<=3
  servers=[w for w in worlds if ue.GameplayStatics.get_game_mode(w)];assert len(servers)==1
  C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();HC=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
  pawns=list(ue.GameplayStatics.get_all_actors_of_class(servers[0],C));assert len(pawns)==2
  ids={p.player_state.player_id for p in pawns};assert len(ids)==2
  targets=[('control',control)]
  descendants=[w for w in ue.ObjectIterator(ue.Widget) if w.get_outer() and w.get_outer().get_outer()==control]
  assert len(descendants)==9;targets.extend(('control-designer-'+w.get_name(),w) for w in descendants)
  owner_ids=[]
  for world in worlds:
   peer=list(ue.GameplayStatics.get_all_actors_of_class(world,C));assert {p.player_state.player_id for p in peer}==ids
   for p in peer:
    if not p.is_locally_controlled():continue
    owner=p.get_controller();assert owner and owner.is_local_controller()
    components=p.get_components_by_class(HC);assert len(components)==1
    hud=components[0].get_editor_property('HUDWidget');prompt=p.get_editor_property('PromptWidget');assert hud and prompt
    assert all(w.get_owning_player()==owner and w.is_in_viewport() for w in (hud,prompt))
    targets.extend((('HUD-'+str(p.player_state.player_id),hud),('prompt-'+str(p.player_state.player_id),prompt)))
    owner_ids.append(p.player_state.player_id)
  assert set(owner_ids)==ids and len(owner_ids)==2 and len(targets)==14
  rows=[]
  for kind,w in targets:
   assert w and w.get_world()==(pc.get_world() if kind.startswith('control') else w.get_owning_player().get_world())
   # NO FGeometry crosses Python for internal_result. The same exact widget is
   # measured again through the existing Python path for a paired comparison.
   internal=vec(cdo.call_method(FUNCTION,args=(w,)))
   python=vec(ue.SlateLibrary.get_local_size(w.get_cached_geometry()))
   rows.append({'kind':kind,'widget':ref(w),'class':ref(w.get_class()),'world':ref(w.get_world()),
    'internal_vector2d':internal,'python_geometry_roundtrip':python,'desired':vec(w.get_desired_size()),
    'internal_positive':positive(internal),'python_positive':positive(python),'equal':internal==python})
  assert disk_hashes()==original
  R.update({'blueprint_path':receipt['blueprint_path'],'build_receipt_sha256':sha(BUILD),
   'control_receipt':str(BASE/(control_name+'.json')),'control_receipt_sha256':sha(BASE/(control_name+'.json')),
   'control':ref(control),'owner_controller':ref(pc),'owner_world':ref(pc.get_world()),'rows':rows,
   'internal_control_positive':rows[0]['internal_positive'],
   'measured_boundary_divergence':any(r['internal_positive'] and not r['python_positive'] for r in rows),
   'saved_bytes_preserved':True,'protected_disk_hashes_after':disk_hashes(),
   'collection_complete':True,'passed':True,'status':'paired_measurements_collected_no_hud_fix_claim'})
  write(R)
except Exception:
 R.update({'error':traceback.format_exc(),'passed':False,'status':'build_or_measure_failed'})
 if 'original' in globals():
  R['protected_disk_hashes_after']=disk_hashes();R['saved_bytes_preserved']=disk_hashes()==original
 write(R)
