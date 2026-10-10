"""Original HC2 pickup chime. No samples, generators, or external assets."""
import math,wave,struct,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[3]
folder=root/'SourceArt/HC/HC2';folder.mkdir(parents=True,exist_ok=True)
path=folder/'SFX_RelicPickup.wav'
assert not path.exists(),'Refuse source overwrite'
rate=48000;duration=.32;values=[]
for i in range(int(rate*duration)):
 t=i/rate
 def tone(start,freq):
  u=t-start
  return 0 if u<0 else (1-math.exp(-u*750))*math.exp(-u*18)*(math.sin(2*math.pi*freq*u)+.18*math.sin(2*math.pi*freq*2*u))
 sample=.14*tone(0,1046.502261)+.13*tone(.075,1318.510228)
 values.append(int(max(-1,min(1,sample))*32767))
with wave.open(str(path),'wb') as out:
 out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate);out.writeframes(struct.pack('<'+'h'*len(values),*values))
manifest={'source':str(path.relative_to(root)).replace('\\','/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':len(values),'rate_hz':rate,'channels':1,'duration_seconds':duration,'peak_sample':max(abs(x) for x in values),'tool':'Python standard library wave/math; team-authored deterministic additive synthesis','tool_url':'https://docs.python.org/3/library/wave.html','plan':'local, no paid generator','license':'original team-authored work; no third-party samples or attribution; public repository redistribution permitted','attribution':'none required','destination':'/Game/Core/Audio/SFX_RelicPickup'}
(folder/'provenance.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
