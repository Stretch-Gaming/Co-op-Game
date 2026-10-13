import json,gzip,sys
sys.path.insert(0,str(HERE))
from context import *
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()
data=json.loads(gzip.decompress((QUEUE/'scene.json.gz').read_bytes()))
expected={'MazeLevel_Source_'+str(r['source_index']):r['location'] for r in data['components']}
expected.update({'MazeVariety_'+p['id']:p['location'] for c in data['layout']['clusters'] for p in c['primitives']})
wrong=[]
for a in actors:
    label=a.get_actor_label()
    if label not in expected:continue
    actual=a.get_actor_location();desired=expected[label]
    if (actual-ue.Vector(*desired)).length()>.1:wrong.append({'label':label,'actual':[actual.x,actual.y,actual.z],'expected':desired})
RESULT={'wrong_actor_locations':wrong,'checked':len(expected),'passed':not wrong}
(QUEUE/'scene-pose.json').write_text(json.dumps(RESULT,indent=2))
