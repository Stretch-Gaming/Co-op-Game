"""Non-destructive PCM signal QC. Exit2 only for invalid PCM/inputs; heuristics warn."""
import argparse,array,json,math,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
def require(ok,msg):
 if not ok:raise ValueError(msg)
def db(v):return round(20*math.log10(max(abs(v),1e-12)),3)
def pcm(path):
 d=Path(path).read_bytes();require(d[:4]==b'RIFF' and d[8:12]==b'WAVE','Not RIFF/WAVE');require(struct.unpack_from('<I',d,4)[0]+8==len(d),'RIFF length mismatch')
 pos=12;fmt=None;payload=None
 while pos+8<=len(d):
  tag=d[pos:pos+4];size=struct.unpack_from('<I',d,pos+4)[0];chunk=d[pos+8:pos+8+size];require(len(chunk)==size,'Truncated chunk')
  if tag==b'fmt ':require(fmt is None,'Duplicate fmt');fmt=chunk
  if tag==b'data':require(payload is None,'Duplicate data');payload=chunk
  pos+=8+size+(size%2)
 require(fmt is not None and payload is not None,'Missing fmt/data')
 tag,ch,rate,br,align,bits=struct.unpack_from('<HHIIHH',fmt);require(ch==1 and rate>0 and bits in (16,24,32),'Requires mono integer PCM16/24/32')
 if tag==65534:require(len(fmt)>=40 and fmt[24:40]==bytes.fromhex('0100000000001000800000aa00389b71') and struct.unpack_from('<H',fmt,18)[0]==bits,'Extensible must be full-width PCM')
 else:require(tag==1,'Not integer PCM')
 require(align==bits//8 and br==rate*align and len(payload)%align==0 and len(payload)>0,'Invalid frame layout')
 integers=[int.from_bytes(payload[p:p+align],'little',signed=True) for p in range(0,len(payload),align)]
 scale=2**(bits-1);x=array.array('d',(i/scale for i in integers)); full=[i==scale-1 or i==-scale for i in integers]
 return x,rate,{'full_scale_samples':sum(full),'full_scale_longest_run':longest(full),'bits':bits}
def longest(flags):
 best=run=0
 for f in flags:
  run=run+1 if f else 0;best=max(best,run)
 return best
def intervals(flags,step,min_seconds):
 runs=[];start=None
 for i,f in enumerate(list(flags)+[False]):
  if f and start is None:start=i
  if not f and start is not None:
   if (i-start)*step>=min_seconds:runs.append({'start':round(start*step,3),'end':round(i*step,3),'seconds':round((i-start)*step,3)})
   start=None
 return runs
def analyze(x,rate,loop=False):
 require(len(x)>1,'Too few samples');peak=max(map(abs,x));mean=sum(x)/len(x);rms=math.sqrt(sum(v*v for v in x)/len(x));steps=sorted(abs(b-a) for a,b in zip(x,x[1:]));q=lambda p:steps[min(int(p*(len(steps)-1)),len(steps)-1)]
 block=max(1,int(rate*.1));rms_blocks=[math.sqrt(sum(v*v for v in x[i:i+block])/len(x[i:i+block])) for i in range(0,len(x),block)]
 r={'seconds':len(x)/rate,'sample_peak_dbfs':db(peak),'true_peak':'not measured','rms_dbfs':db(rms),'dc_signed':mean,'dc_dbfs':db(mean),'zero_sample_count':sum(v==0 for v in x),'derivative_median_dbfs':db(q(.5)),'derivative_p99_dbfs':db(q(.99)),'derivative_max_dbfs':db(steps[-1]),'low_rms_intervals_below_minus60':intervals([v<.001 for v in rms_blocks],block/rate,.5),'near_silence_intervals_below_minus80':intervals([v<.0001 for v in rms_blocks],block/rate,.5),'warnings':[]}
 if abs(mean)>.001:r['warnings'].append('DC exceeds0.1percent fullscale; inspect before choosing highpass')
 if not peak:r['warnings'].append('Entire signal zero')
 if r['near_silence_intervals_below_minus80']:r['warnings'].append('Long near-silence windows; may be intentional')
 if loop:
  seam=abs(x[0]-x[-1]);w=max(2,int(rate*.005));cross=list(x[-w:])+list(x[:w]);derivatives=[abs(b-a) for a,b in zip(cross,cross[1:])]
  r['loop']={'endpoint_step_dbfs':db(seam),'endpoint_vs_natural_p99':seam/max(q(.99),1e-12),'crossboundary_10ms_derivative_rms_dbfs':db(math.sqrt(sum(v*v for v in derivatives)/len(derivatives))),'crossboundary_10ms_derivative_max_dbfs':db(max(derivatives)),'last5ms_rms_dbfs':db(math.sqrt(sum(v*v for v in x[-w:])/len(x[-w:]))),'first5ms_rms_dbfs':db(math.sqrt(sum(v*v for v in x[:w])/len(x[:w])))}
  if seam>.01 and seam>8*q(.99):r['warnings'].append('Endpoint step >-40dBFS and8times naturalp99; listen for click')
 return r
def mix(a,b,gain_b=.5,offset=0):
 require(len(a)==len(b) and len(a)>0,'Mix needs equal nonempty sample counts')
 values=[v+gain_b*b[(i+offset)%len(b)] for i,v in enumerate(a)];return {'sample_peak_dbfs':db(max(map(abs,values))),'over_fullscale_samples':sum(abs(v)>1 for v in values),'over_fullscale_longest_run':longest(abs(v)>1 for v in values)}
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args(argv)
 report={'mode':'read_only_signal_analysis','structural_errors':[],'files':{},'mix':{},'listening_performed':False};loaded={}
 files=sorted(args.source.glob('*.wav'))
 if not files:report['structural_errors'].append('No WAV inputs')
 for f in files:
  try:
   x,rate,meta=pcm(f);r=analyze(x,rate,'Loop' in f.stem);r.update(meta);r['rate']=rate
   if meta['full_scale_samples']:r['warnings'].append('Full-scale sample(s); hard clipping suspected only if repeated plateau, intentional distortion possible')
   report['files'][f.name]=r
   if f.stem.startswith('SFX_Chase_'):loaded[f.stem]=(x,rate)
  except (ValueError,struct.error,OSError) as e:report['structural_errors'].append(f.name+': '+str(e))
 names=('SFX_Chase_Loop_2D','SFX_Chase_Build_Loop_2D')
 if all(n in loaded for n in names):
  (a,rate),(b,rb)=(loaded[n] for n in names)
  if rate!=rb or len(a)!=len(b):report['mix']['warning']='Chase sample counts/rates mismatch; phase-preserving playback needs review'
  else:
   report['mix']={'volumes':[1,.5],'aligned':mix(a,b),'duration_match':True,'offset_stress_not_actual_playback':{str(ms):mix(a,b,offset=int(rate*ms/1000)) for ms in (125,250,500,1000)},'peak_bound_dbfs':db(max(map(abs,a))+.5*max(map(abs,b))),'limit':'Mono additive source model; no attenuation, dynamics, bus gain, codec or engine spatialization modeled. Sample peak only.'}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'files':len(report['files']),'structural_errors':report['structural_errors'],'warning_files':[n for n,r in report['files'].items() if r['warnings']],'mix':report['mix']}));return 2 if report['structural_errors'] else 0
if __name__=='__main__':raise SystemExit(main())
