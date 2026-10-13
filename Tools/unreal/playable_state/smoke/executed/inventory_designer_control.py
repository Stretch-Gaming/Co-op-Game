"""Parent-only read-only designer-tree inventory. No widget/asset creation.

Uses installed UMGToolSet.GetWidgets; verifies an existing template candidate
before any PIE control instance is made. Reads four exact existing assets only.
"""
import hashlib,json,re,time,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
EXPECTED=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
args=globals().get('ARGS',{});name=args.get('report_name','designer-control-inventory')
assert re.fullmatch(r'[A-Za-z0-9_-]+',name)
OUT=Path('/tmp/coop-audit/runtime-evidence')/(name+'.json')
PATHS=('/Game/VehicleTemplate/UI/UI_Vehicle','/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD',
       '/Game/Puzzles/UI/WBP_InteractPrompt','/Game/Puzzles/UI/Results/WBP_RunResults')
R={'schema':1,'read_only':True,'collection_complete':False,'assets':[],
   'packages_saved':[],'rendered_pixel_acceptance':False,'native_log_scan_pending':True}
start=time.monotonic()
def ref(o):return o.get_path_name() if o else None
def listed(obj,names):
 raw=OBJ.list_properties(obj);schema=json.loads(raw) if raw.strip() else {}
 schema=schema.get('properties',schema)
 normal=lambda value:str(value).replace('_','').lower()
 selected={name:next((k for k in schema if normal(k)==normal(name)),None) for name in names}
 actual=[k for k in selected.values() if k]
 return {'listed':actual,'unavailable':[k for k,v in selected.items() if not v],
         'values':json.loads(OBJ.get_properties(obj,actual)) if actual else {}}
try:
 assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
 library=ue.load_object(None,'/Script/UMGToolSet.Default__UMGToolSet')
 assert library,'Installed UMGToolSet CDO is not loaded/available; do not replace with asset authoring calls'
 for path in PATHS:
  assert time.monotonic()-start<5,'Bounded four-asset inventory exceeded five seconds'
  bp=ue.load_asset(path);assert bp and bp.get_class().get_name()=='WidgetBlueprint',path
  disk=EXPECTED/'Content'/(path.removeprefix('/Game/')+'.uasset');original=hashlib.sha256(disk.read_bytes()).hexdigest()
  tree=library.call_method('GetWidgets',args=(bp,));info=tree.info;widgets=list(tree.widgets)
  assert len(widgets)<=64,'Designer tree exceeds bounded inventory'
  rows=[]
  for item in widgets:
   w=item.widget
   rows.append({'name':str(item.widget_name),'path':ref(w),'class':ref(w.get_class()),
       'parent':ref(item.parent),'named_slot_host':ref(item.named_slot_host),'slot':ref(item.slot),
       'is_variable':bool(item.is_variable),'inherited':bool(item.inherited),
       'visibility':str(w.get_visibility()),'opacity':float(w.get_render_opacity()),
       'stored_properties':listed(w,['Text','Visibility','RenderOpacity'])})
  assert hashlib.sha256(disk.read_bytes()).hexdigest()==original,'Read-only inventory changed saved bytes'
  R['assets'].append({'asset':path,'generated_class':ref(bp.generated_class()),
      'parent_class':ref(info.parent_class),'root_widget_class':ref(info.root_widget_class),
      'widget_count':int(info.widget_count),'named_slot_count':int(info.named_slot_count),
      'widgets':rows,'saved_asset_sha256':original,'saved_bytes_unchanged':True})
 R['collection_complete']=True
except Exception:R['error']=traceback.format_exc()
R['elapsed_seconds']=round(time.monotonic()-start,6)
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(R,indent=2))
