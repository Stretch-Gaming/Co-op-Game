import math,struct,tempfile,unittest
from pathlib import Path
from check_audio import pcm,analyze,mix,main

def wav(samples,ext=False):
 rate=48000;fmt=struct.pack('<HHIIHH',65534 if ext else 1,1,rate,rate*3,3,24)
 if ext:fmt+=struct.pack('<HHI',22,24,0)+bytes.fromhex('0100000000001000800000aa00389b71')
 payload=b''.join(int(v).to_bytes(3,'little',signed=True) for v in samples)
 body=b'WAVE'+b'fmt '+struct.pack('<I',len(fmt))+fmt+b'data'+struct.pack('<I',len(payload))+payload+(b'\0' if len(payload)%2 else b'')
 return b'RIFF'+struct.pack('<I',len(body))+body
class QualityTests(unittest.TestCase):
 def load(self,values,ext=False):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.wav';p.write_bytes(wav(values,ext));return pcm(p)
 def test_24bit_sign_extensible(self):
  x,rate,meta=self.load([-8388608,-1,0,1,8388607],True)
  self.assertEqual(x[0],-1);self.assertEqual(x[1],-1/8388608);self.assertEqual(meta['full_scale_samples'],2);self.assertEqual(rate,48000)
 def test_zero_dc_plateau(self):
  x,rate,_=self.load([0]*48000);r=analyze(x,rate);self.assertEqual(r['zero_sample_count'],48000);self.assertIn('Entire signal zero',r['warnings'])
  x,rate,_=self.load([100000]*100);r=analyze(x,rate);self.assertGreater(r['dc_signed'],.01);self.assertTrue(r['warnings'])
  _,_,m=self.load([8388607]*7+[0]+[-8388608]*3);self.assertEqual(m['full_scale_longest_run'],7)
 def test_smooth_broken_loop(self):
  a=[.2*math.sin(2*math.pi*i/48000) for i in range(48000)];self.assertFalse(analyze(a,48000,True)['warnings'])
  a[-1]=.9;self.assertTrue(any('Endpoint step' in w for w in analyze(a,48000,True)['warnings']))
 def test_mix(self):
  r=mix([.8,-.8],[.8,-.8]);self.assertEqual(r['over_fullscale_samples'],2);self.assertEqual(r['over_fullscale_longest_run'],2)
  self.assertEqual(mix([.4,-.4],[.4,-.4],offset=1)['over_fullscale_samples'],0)
  with self.assertRaises(ValueError):mix([.1],[.1,.2])
 def test_exit_only_structural(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'zero.wav').write_bytes(wav([0]*100));self.assertEqual(main([tmp,'--output',str(p/'result.json')]),0)
   (p/'bad.wav').write_bytes(b'RIFFbroken');self.assertEqual(main([tmp,'--output',str(p/'result.json')]),2)
if __name__=='__main__':unittest.main()
