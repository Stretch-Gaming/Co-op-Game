import base64,sys
from rpc import call,QUEUE
value=call('EditorToolset.EditorAppToolset','CaptureViewport',{'captureTransform':None,'annotations':{'gridSpacing':0,'gridExtent':0,'gridHeight':0,'maxLabelDistance':0,'maxLabels':0},'bShowUI':True})
def encoded(data):
 if isinstance(data,dict):
  for k,v in data.items():
   if isinstance(v,str) and len(v)>1000:return v
   found=encoded(v)
   if found:return found
 if isinstance(data,list):
  for v in data:
   found=encoded(v)
   if found:return found
image=encoded(value);assert image
path=QUEUE/(sys.argv[1] if len(sys.argv)>1 else 'game-view.png');path.write_bytes(base64.b64decode(image));print(path)
