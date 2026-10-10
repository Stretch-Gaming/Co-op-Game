"""Read PCM RIFF/WAVE including WAVE_FORMAT_EXTENSIBLE, without decoding audio."""
import struct
from pathlib import Path
def wav_info(path):
 d=Path(path).read_bytes(); assert d[:4]==b'RIFF' and d[8:12]==b'WAVE'; pos=12; fmt=None; samples=None
 while pos+8<=len(d):
  name=d[pos:pos+4]; size=struct.unpack_from('<I',d,pos+4)[0]; payload=d[pos+8:pos+8+size]; assert len(payload)==size
  if name==b'fmt ': fmt=payload
  elif name==b'data': samples=size
  pos+=8+size+(size%2)
 assert fmt is not None and samples is not None
 tag,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',fmt)
 if tag==65534:
  assert len(fmt)>=40 and fmt[24:40]==bytes.fromhex('0100000000001000800000aa00389b71'),'Extensible WAV must be PCM'
  valid_bits=struct.unpack_from('<H',fmt,18)[0]; assert valid_bits==bits
 else: assert tag==1,'WAV must be integer PCM'
 assert align==channels*bits//8 and byte_rate==rate*align and samples%align==0
 return {'channels':channels,'sample_rate':rate,'bit_depth':bits,'duration':samples/byte_rate,'pcm':True}
