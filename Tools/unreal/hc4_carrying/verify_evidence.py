"""Independent assertions over captured runtime worlds; no Unreal dependency."""
import json,math,pathlib,sys
E=pathlib.Path(__file__).parent/'evidence'
checks=[]
def check(condition,message):
    assert condition,message
    checks.append(message)
def load(name): return json.loads((E/(name+'.json')).read_text())
def validate(name,players,carried,placed=0):
    data=load(name)
    worlds=data['worlds']
    check(len(worlds)>=2,name+': network worlds present')
    server=next(w for w in worlds if w['server'])
    expected={i['name']:i for i in server['items']}
    for w in worlds:
        check(len(w['players'])==players,name+': player count '+w['world'])
        check(sum(i['state']==1 for i in w['items'])==carried,name+': carried count '+w['world'])
        check(sum(i['state']==2 for i in w['items'])==placed,name+': placed count '+w['world'])
        for i in w['items']:
            check(i['state']==expected[i['name']]['state'],name+': replicated state '+i['name'])
            check(i['physics']==(i['state']==0),name+': physics '+i['name'])
            check(('NO_COLLISION' in i['collision'])==(i['state']==1),name+': collision '+i['name'])
            if i['state']==1:
                check(i['carrier'] is not None and i['parent']==i['carrier'],name+': attached carrier '+i['name'])
                p=next(p for p in w['players'] if p['name']==i['carrier'])
                check(p['carried']==i['name'],name+': reciprocal carrying '+i['name'])
                if 'carrier_id' in i:
                    check(i['carrier_id']==expected[i['name']]['carrier_id'],name+': replicated owner identity '+i['name'])
            else:
                check(i['carrier'] is None,name+': released carrier '+i['name'])
            if w['server'] and i['heavy']:
                check(('HC_PlateWeight' in i['tags'])==(i['state']!=1),name+': authoritative plate weight '+i['name'])
        for p in w['players']:
            check(p['components']==1,name+': single component '+p['name'])
            heavy=p['carried'] and expected[p['carried']]['heavy']
            check(p['speed']==(300 if heavy else 600),name+': walk speed '+p['name'])
            check(p['crouch_speed']==(150 if heavy else 300),name+': crouch speed '+p['name'])
        if 'plate_weights' in w:
            if w['server']:
                check(len(w['plate_weights'])==1,name+': server overlap probe present')
                expected_weight=0 if next(i for i in w['items'] if i['name']=='BP_KeyRelic_C_0')['state']==1 else 1
                check(w['plate_weights'][0]['count']==expected_weight,name+': server overlap weight count')
            else: check(w['plate_weights']==[],name+': no client weight calculation')
    return data

for count in [2,3,4]:
    pickups=count
    for stage,num in [('initial',0),('pickup',pickups),('drop',0),('repickup',pickups),('heavy',pickups),('reset',0)]:
        if (E/f'{stage}_{count}.json').exists(): validate(f'{stage}_{count}',count,num)
        elif '--partial' not in sys.argv: raise AssertionError(f'Missing {stage}_{count}')
for stage,carries,places in [('handoff_2',0,1),('competition_2',1,0),('late_join_2',1,0),('late_join_pickup_2',1,0)]:
    validate(stage,2,carries,places)
for stage,carries,places in [('weight_carried_4',1,0),('weight_drop_4',0,0),('weight_placed_4',0,1),('late_join_heavy_4',1,0)]:
    if (E/(stage+'.json')).exists(): validate(stage,4,carries,places)
    elif '--partial' not in sys.argv: raise AssertionError('Missing '+stage)
for stage,carries in [('fresh_client_pickup_4',1),('fresh_client_drop_4',0)]:
    if (E/(stage+'.json')).exists(): validate(stage,4,carries)
    elif '--partial' not in sys.argv: raise AssertionError('Missing '+stage)
for stage,carries,places in [('split_initial',0,0),('split_pickup',2,0),('split_drop_one',1,0),('split_repickup',2,0),('split_handoff',1,1),('split_reset',0,0)]:
    if (E/(stage+'.json')).exists():
        data=validate(stage,4,carries,places)
        check(sum(p['local'] for p in next(w for w in data['worlds'] if w['server'])['players'])==2,stage+': two local host players')
    elif '--partial' not in sys.argv: raise AssertionError('Missing '+stage)
motion_data=load('movement_final_4')
motion=motion_data['samples']
check(len(motion)>=8,'heavy movement: at least eight samples')
locals_by_id={}
for sample in motion:
    for world in sample['worlds']:
        for p in world['players']:
            if p['local']:
                locals_by_id.setdefault(p['id'],[]).append((sample['t'],p))
for pid,rows in locals_by_id.items():
    if not any(abs(r['velocity'][1])>1 for t,r in rows): continue
    p=rows[-1][1]
    expected_speed=300 if p['carried'] else 600
    steady=[r for t,r in rows if 0.8<t<motion_data['duration']-0.2]
    check(len(steady)>=3,f'movement {pid}: steady samples')
    check(all(abs(math.hypot(*r['velocity'][:2])-expected_speed)<1 for r in steady),f'movement {pid}: expected horizontal speed without stalls')
    check(all(b['position'][1]>=a['position'][1]-0.1 for (_,a),(_,b) in zip(rows,rows[1:])),f'movement {pid}: no backward correction')
check(load('client_authority')['passed'],'direct client authority guard checks')
for count in [2,3,4]:
    initial=next(w for w in load(f'initial_{count}')['worlds'] if w['server'])
    reset=next(w for w in load(f'reset_{count}')['worlds'] if w['server'])
    base={i['name']:i for i in initial['items']}
    for item in reset['items']:
        check(math.dist(item['position'][:2],base[item['name']]['position'][:2])<3,f'reset {count}: original XY '+item['name'])
        check(abs(item['position'][2]-base[item['name']]['position'][2])<20,f'reset {count}: original ground height '+item['name'])
summary={'checks':len(checks),'passed':True,'details':checks}
(E/'assertions.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(f'{len(checks)} runtime evidence assertions passed')
