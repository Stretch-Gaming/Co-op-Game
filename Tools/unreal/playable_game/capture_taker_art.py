import base64,sys
from rpc import call,QUEUE
name=sys.argv[1];assert name in ('SM_Taker','SM_TakerArm','MI_Taker_Body','MI_TakerArm_Body','MI_Taker_Eyes')
value=call('EditorToolset.EditorAppToolset','CaptureAssetImage',{'assetPath':'/Game/Player/Art/Taker/'+name})
def encoded(v):
 if isinstance(v,str) and len(v)>1000:return v
 if isinstance(v,dict):
  for x in v.values():
   b=encoded(x)
   if b:return b
 if isinstance(v,list):
  for x in v:
   b=encoded(x)
   if b:return b
b=encoded(value);assert b
path=QUEUE/(name+'-native.png');path.write_bytes(base64.b64decode(b));print(path)
