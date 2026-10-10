import unittest
from types import SimpleNamespace as NS
from hit_codec import decode
class FakeHit:
 def __init__(self,fields=None,text=''):self.fields=fields or {};self.text=text
 def get_editor_property(self,name):
  if name not in self.fields:raise Exception('not exposed')
  return self.fields[name]
 def export_text(self):return self.text
class HitCodecTests(unittest.TestCase):
 def test_nonblocking_truthy_struct_is_not_blocker(self):
  hit=FakeHit({'blocking_hit':False});self.assertTrue(hit);self.assertIsNone(decode(hit))
 def test_explicit_false_export_is_not_blocker(self):self.assertIsNone(decode(FakeHit(text='(bBlockingHit=False)')))
 def test_native_reflected_vectors_and_distance(self):
  fields={'blocking_hit':True,'start_penetrating':False,'distance':42.,'location':NS(x=1,y=2,z=3),'impact_point':NS(x=1,y=2,z=3),'impact_normal':NS(x=0,y=0,z=1),'component':None};data=decode(FakeHit(fields));self.assertEqual(data['distance_cm'],42);self.assertEqual(data['impact_point'],[1,2,3]);self.assertTrue(data['blocking'])
 def test_explicit_export_fallback(self):
  text='(bBlockingHit=True,bStartPenetrating=False,Distance=10.5,Location=(X=1,Y=2,Z=3),ImpactPoint=(X=1,Y=2,Z=3),ImpactNormal=(X=0,Y=0,Z=1))';data=decode(FakeHit(text=text));self.assertEqual(data['field_methods']['blocking'],'export_text');self.assertEqual(data['impact_normal'],[0,0,1])
 def test_recorded_protected_native_result_preserves_component_identity(self):
  import json
  from pathlib import Path
  example=json.loads((Path(__file__).parent/'evidence/native-hit-example.json').read_text())
  data=decode(FakeHit(text=example['export_text']))
  self.assertTrue(data['blocking']);self.assertEqual(data['distance_cm'],200.)
  self.assertEqual(data['impact_point'],[-175.,9250.,-300.])
  self.assertTrue(data['component_native_path'].endswith('StaticMeshActor_995.StaticMeshComponent0'))
 def test_unsupported_blocking_data_fails_closed(self):
  with self.assertRaises(RuntimeError):decode(FakeHit(text='(Unknown=True)'))
if __name__=='__main__':unittest.main()
