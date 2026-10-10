"""Read reflected native HitResult fields, falling back to explicit export tokens only."""
import re
NUMBER=r'[-+0-9.eE]+'
def prop(hit,name):
 try:return hit.get_editor_property(name),True
 except Exception:return None,False
def boolean(hit,name,export_name,text,required=True):
 value,available=prop(hit,name)
 if available and isinstance(value,bool):return value,'reflection'
 match=re.search(r'\b'+export_name+r'=(True|False|true|false)',text)
 if match:return match[1].lower()=='true','export_text'
 if required:raise RuntimeError('Unsupported HitResult: explicit '+export_name+' unavailable')
 return None,'unavailable'
def scalar(hit,name,export_name,text):
 value,available=prop(hit,name)
 if available:return float(value),'reflection'
 match=re.search(r'\b'+export_name+r'=('+NUMBER+r')',text)
 if not match:raise RuntimeError('Unsupported HitResult: '+export_name)
 return float(match[1]),'export_text'
def vector(hit,name,export_name,text):
 value,available=prop(hit,name)
 if available:return [float(value.x),float(value.y),float(value.z)],'reflection'
 match=re.search(r'\b'+export_name+r'=\(X=('+NUMBER+r'),Y=('+NUMBER+r'),Z=('+NUMBER+r')\)',text)
 if not match:raise RuntimeError('Unsupported HitResult: '+export_name)
 return [float(v)for v in match.groups()],'export_text'
def decode(hit):
 if hit is None:return None
 text=hit.export_text();blocking,method=boolean(hit,'blocking_hit','bBlockingHit',text)
 if not blocking:return None # Native structs can exist even when the trace did not block.
 data={'blocking':True,'native_hit_export':text,'field_methods':{'blocking':method}}
 for key,name,export_name in [('initial_overlap','start_penetrating','bStartPenetrating')]:
  data[key],data['field_methods'][key]=boolean(hit,name,export_name,text,False)
 data['distance_cm'],data['field_methods']['distance_cm']=scalar(hit,'distance','Distance',text)
 for name,export_name in [('location','Location'),('impact_point','ImpactPoint'),('impact_normal','ImpactNormal')]:data[name],data['field_methods'][name]=vector(hit,name,export_name,text)
 match=re.search(r"\bComponent=\"[^\"']*'([^']+)'\"",text)
 data['component_native_path']=match.group(1) if match else None
 component,available=prop(hit,'component');actor=None
 if component and hasattr(component,'get_owner'):actor=component.get_owner()
 if not actor and hasattr(hit,'get_actor'):actor=hit.get_actor()
 data.update({'actor_label':actor.get_actor_label()if actor else None,'actor_path':actor.get_path_name()if actor else None,'component':component.get_path_name()if component else None,'hidden_actor':actor.is_hidden()if actor else None,'identity_method':'reflected component owner'if component else'get_actor'if actor else'unavailable'})
 return data
