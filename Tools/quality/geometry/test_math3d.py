import unittest
from math3d import rotate,position,normal,triangle,slope_degrees,passage_fits
class GeometryMathTests(unittest.TestCase):
 def test_horizontal_floor_centroid_and_area(self):
  t=triangle([0,0,0],[100,0,0],[0,100,0]);self.assertEqual(t['area'],5000);self.assertEqual(t['normal'],[0,0,1]);self.assertEqual(slope_degrees(t['normal']),0)
 def test_yaw_and_pitch_transform(self):
  v=rotate([100,0,0],[0,90,0]);self.assertAlmostEqual(v[0],0,places=8);self.assertAlmostEqual(v[1],100)
  v=rotate([100,0,0],[30,0,0]);self.assertAlmostEqual(v[2],50);self.assertAlmostEqual(slope_degrees(rotate([0,0,1],[30,0,0])),30)
 def test_scaled_translated_floor(self):
  r={'rotation':[0,90,0],'scale':[2,3,1],'location':[-175,3200,400]};p=position([10,0,0],r);self.assertAlmostEqual(p[0],-175);self.assertAlmostEqual(p[1],3220);self.assertAlmostEqual(p[2],400);self.assertEqual(normal([0,0,1],r),[0,0,1])
 def test_nonuniform_scale_normal(self):
  r={'rotation':[0,0,0],'scale':[2,1,1],'location':[0,0,0]};n=normal([1,0,1],r);self.assertAlmostEqual(n[0]/n[2],.5)
 def test_narrow_passage_uses_capsule_diameter_and_margin(self):
  self.assertFalse(passage_fits(67,34));self.assertFalse(passage_fits(75,34));self.assertTrue(passage_fits(76,34));self.assertFalse(passage_fits(76,40))
 def test_degenerate_floor_not_walkable(self):self.assertEqual(triangle([0,0,0],[0,0,0],[0,0,0])['area'],0)
if __name__=='__main__':unittest.main()
