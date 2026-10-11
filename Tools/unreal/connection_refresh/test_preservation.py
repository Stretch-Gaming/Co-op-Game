import unittest
from types import SimpleNamespace as NS
from preservation import signature,first_difference
class PointerTransform(NS):
 def __repr__(self):return '<Transform at '+hex(id(self))+'>'
class FakeActor:
 tags=['ConnectedEnvironment','ConnectionDoor']
 def __init__(self):self.x=325.
 def get_path_name(self):return '/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze.Connected_Door'
 def get_actor_transform(self):return PointerTransform(translation=NS(x=self.x,y=1400.,z=200.),rotation=NS(x=0.,y=0.,z=0.,w=1.),scale3d=NS(x=1.,y=1.,z=1.))
class PreservationTests(unittest.TestCase):
 def test_new_transform_objects_have_equal_numeric_signature(self):
  actor=FakeActor();a=actor.get_actor_transform();b=actor.get_actor_transform();self.assertNotEqual(str(a),str(b));self.assertEqual(signature(actor),signature(actor));self.assertIsNone(first_difference([signature(actor)],[signature(actor)]))
 def test_real_movement_has_first_field_evidence(self):
  actor=FakeActor();before=[signature(actor)];actor.x+=1.;diff=first_difference(before,[signature(actor)]);self.assertEqual(diff['index'],0);self.assertEqual(diff['fields'],{'translation':{'before':[325.,1400.,200.],'after':[326.,1400.,200.]}})
 def test_rotation_scale_and_tags_are_checked(self):
  before=signature(FakeActor())
  for field,value in [('rotation_quaternion',[0,0,1,0]),('scale',[2,1,1]),('tags',[])]:
   after=dict(before);after[field]=value;self.assertIn(field,first_difference([before],[after])['fields'])
 def test_count_difference_reported(self):self.assertEqual(first_difference([], [signature(FakeActor())]),{'count_before':0,'count_after':1})
if __name__=='__main__':unittest.main()
