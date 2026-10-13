"""Compact native receipts without importing Unreal or copying full graph dumps.

The editor owner supplies completed raw files. --complete checks report coverage;
it never converts missing log checks, failed cases or fixtures into acceptance.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CASES=('retarget_death','all_dead','flare_all_safe','destroyed_target','flare_backoff')
ERROR_RE=re.compile(r'Blueprint Runtime Error|Accessed None|\bError:|\bFatal(?: error)?\b|Assertion failed',re.I)

def read(path):
    return json.loads(path.read_text())

def receipt(path):
    return {'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def error_tail(value):
    return str(value).strip().splitlines()[-1] if value else None

def native_log(path,data):
    logfile=path.with_name(path.stem+'-log.txt')
    result={'receipt':receipt(logfile) if logfile.is_file() else None,'scanned_error_count':None}
    if logfile.is_file():
        errors=[line for line in logfile.read_text(errors='replace').splitlines() if ERROR_RE.search(line)]
        result.update({'scanned_error_count':len(errors),'error_excerpt':errors[:5]})
    reported=data.get('native_log_errors')
    if reported is not None:
        if isinstance(reported,list):result['owner_reported_error_count']=len(reported)
        elif isinstance(reported,int) and not isinstance(reported,bool):result['owner_reported_error_count']=reported
        else:raise ValueError('Unrecognized native_log_errors in '+path.name)
    counts=[result[k] for k in ('scanned_error_count','owner_reported_error_count') if result.get(k) is not None]
    result['clean']=all(c==0 for c in counts) if counts else None
    return result

def run_summary(path):
    data=read(path)
    worlds=data.get('world_inventory',[])
    server=[w for w in worlds if w.get('authoritative_game_mode')]
    client=[w for w in worlds if not w.get('authoritative_game_mode')]
    owners=[i for w in worlds for i in w.get('local_player_ids',[])]
    profile=data.get('profile');n=data.get('players')
    host_count=sum(len(w.get('local_player_ids',[])) for w in server)
    expected_host=0 if profile=='joining' else 2
    expected_clients=n if profile=='joining' else n-2 if isinstance(n,int) else None
    topology=(profile in ('joining','host_split') and n in (2,3,4) and len(server)==1
              and len(client)==expected_clients and host_count==expected_host
              and len(owners)==len(set(owners))==n)
    drops=[{k:s[k] for k in ('phase','server_local_time','shortened_from','backoff_until','flare_distance_cm') if k in s}
           for s in data.get('ghost_samples',[]) if 'shortened_from' in s]
    log=native_log(path,data)
    passed=bool(data.get('passed'))
    return {'receipt':receipt(path),'case':data.get('case'),'profile':profile,'players':n,
            'passed':passed,'error':error_tail(data.get('error')),'cleanup_errors':data.get('cleanup_errors',[]),
            'checks':[c.get('name') for c in data.get('checks',[])],
            'topology':{'verified':topology,'server_local_ids':[i for w in server for i in w.get('local_player_ids',[])],
                        'joining_local_ids':[i for w in client for i in w.get('local_player_ids',[])],
                        'network_modes':[w.get('net_mode_from_public_network_queries') for w in worlds]},
            'fixture_counts':dict(Counter(f.get('kind','unspecified') for f in data.get('fixture_actions',[]))),
            'deadline_decreased':data.get('deadline_decreased'),
            'observed_deadline_decreases':drops,'native_log':log,
            'qualified':passed and topology and log['clean'] is True and not data.get('cleanup_errors')}

def patch_summary(path):
    data=read(path);before=deepcopy(data.get('before',{}));after=deepcopy(data.get('after',{}))
    graph='RefreshFlareRepulsion';new_names=set(data.get('created_nodes',[]))
    preflight=data.get('preflight',{});old_source=tuple(preflight.get('original_source',[]))
    setter=(preflight.get('setter'),'BackoffUntil')
    comparable=before and after and graph in before and graph in after and len(old_source)==2 and setter[0]
    preserved=False
    if comparable:
        normalized_before=deepcopy(before);normalized_after=deepcopy(after)
        for node_name,node in normalized_before[graph].items():
            for key,pin in node['pins'].items():
                own=(node_name,key.split(':',1)[1])
                remove=setter if own==old_source else old_source if own==setter else None
                if remove:pin['links']=[link for link in pin['links'] if tuple(link)!=remove]
        for name in new_names:normalized_after[graph].pop(name,None)
        for node in normalized_after[graph].values():
            for pin in node['pins'].values():pin['links']=[link for link in pin['links'] if link[0] not in new_names]
        preserved=normalized_before==normalized_after
    unchanged=[name for name in before if name!=graph and after.get(name)==before[name]]
    deleted=sorted(set(before.get(graph,{}))-set(after.get(graph,{})))
    added=sorted(set(after.get(graph,{}))-set(before.get(graph,{})))
    exec_before={name:{node:{key:pin for key,pin in info['pins'].items() if pin['type'].lower()=='exec'}
                       for node,info in nodes.items()} for name,nodes in before.items()}
    exec_after={name:{node:{key:pin for key,pin in info['pins'].items() if pin['type'].lower()=='exec'}
                      for node,info in nodes.items() if node in before.get(name,{})} for name,nodes in after.items()}
    exec_equal=exec_before==exec_after
    verified=(bool(data.get('passed')) and bool(data.get('saved')) and preserved and exec_equal
              and not deleted and added==sorted(new_names) and len(new_names)==2
              and len(unchanged)==len(before)-1 and set(before)==set(after))
    return {'receipt':receipt(path),'passed':data.get('passed'),'status':data.get('status'),
            'saved_only':data.get('mutation_manifest',{}).get('save_only'),'compile':data.get('compile'),
            'errors':data.get('errors',[]),'graph':graph,'graphs_audited':len(before),
            'original_graph_nodes':len(before.get(graph,{})),'added_nodes':added,'deleted_original_nodes':deleted,
            'unchanged_other_graph_count':len(unchanged),'original_exec_links_preserved':exec_equal,
            'original_nodes_defaults_and_wires_preserved_except_authorized_data_edge':preserved,
            'preservation_verified':bool(verified),'replacement':data.get('mutation_manifest',{}).get('replacement'),
            'before_dsl':data.get('before_dsl'),'after_dsl':data.get('after_dsl')}


def inventory_summary(path):
    data=read(path)
    asset=data['assets']['/Game/Player/Ghosts/BP_Ghost']
    nodes=asset['graphs']['EventGraph']['nodes'];by_name={node['name']:node for node in nodes}
    guards=[]
    for node in nodes:
        if node.get('type_id')!='Utilities|IsValid':continue
        for pin in node['pins']:
            if pin['direction']!='input' or pin['name']!='InputObject':continue
            if any(link['pin']=='Target' and by_name[link['node']].get('type_id','').endswith('|GetTarget') for link in pin['links']):
                guards.append({'node':node['name'],'type_id':node['type_id'],'input':pin['name']})
    return {'receipt':receipt(path),'completed':data.get('completed'),'errors':data.get('errors',[]),
            'engine':data.get('engine'),'ghost_status':asset.get('blueprint_status'),
            'ghost_errors':asset.get('errors',[]),'target_validity_guards':guards,
            'scope':'Loaded native inventory before repair; patch preservation audit retains EventGraph.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch-report',type=Path,required=True)
    parser.add_argument('--baseline-report',type=Path,required=True)
    parser.add_argument('--runtime-dir',type=Path,required=True)
    parser.add_argument('--inventory-report',type=Path)
    parser.add_argument('--output',type=Path,default=HERE/'evidence/summary.json')
    parser.add_argument('--executed-script',type=Path,action='append',default=[])
    parser.add_argument('--host-split-case',choices=CASES,action='append',default=[])
    parser.add_argument('--complete',action='store_true',help='Require every joining case and the explicitly named host subset to be present')
    args=parser.parse_args()
    patch=patch_summary(args.patch_report);baseline=run_summary(args.baseline_report)
    paths=sorted(args.runtime_dir.glob('ghost-*.json'));runs=[run_summary(p) for p in paths]
    keys=[(r['profile'],r['players'],r['case']) for r in runs]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate topology/case receipts; separate attempts before final collection')
    expected=[('joining',n,c) for n in (2,3,4) for c in CASES]
    expected += [('host_split',4,c) for c in args.host_split_case]
    missing=[list(key) for key in expected if key not in keys]
    if args.complete and missing:raise ValueError('Matrix still missing: '+repr(missing))
    if args.complete and not args.host_split_case:raise ValueError('Explicitly name the actual host-split subset; do not imply broader host coverage')
    final=next((r for r in runs if (r['profile'],r['players'],r['case'])==('joining',2,'flare_backoff')),None)
    result={'schema':1,'purpose':'bounded ghost backoff repair and target qualification',
            'collection_complete':bool(args.complete and not missing),'full_mission_acceptance':False,
            'inventory':inventory_summary(args.inventory_report) if args.inventory_report else None,
            'patch':patch,'baseline':baseline,'two_joining_client_final':final,
            'input_method':'Synthetic Enhanced Input through actual owning local-player subsystems and production Blueprint/RPC paths.',
            'baseline_reproduced':baseline['passed'] is False and baseline['deadline_decreased'] is True and bool(baseline['observed_deadline_decreases']),
            'matrix':{'required_joining_players':[2,3,4],'cases':list(CASES),'requested_host_split_subset':args.host_split_case,
                      'missing':missing,'runs':runs,'all_collected_runs_qualified':bool(runs) and all(r['qualified'] for r in runs)},
            'saved_ghost':{'asset':'Content/Player/Ghosts/BP_Ghost.uasset',**receipt(ROOT/'Content/Player/Ghosts/BP_Ghost.uasset')},
            'executed_script_receipts':[receipt(path) for path in args.executed_script],
            'durable_helper_receipts':[receipt(path) for path in sorted(HERE.glob('*.py'))],
            'limits':['Fresh Lobby isolation and disclosed poses/ghost spawn/lethal damage/pawn destruction fixtures.',
                      'Pawn destruction is not a real network Logout test.',
                      'No continuous escape, carrier-first/contact timing, physical-device, packet-emulation or rendered/audio acceptance.']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'summary':str(args.output),'bytes':args.output.stat().st_size,
                      'collection_complete':result['collection_complete'],'runs':len(runs),
                      'patch_preservation_verified':patch['preservation_verified'],'missing':missing},indent=2))

if __name__=='__main__':main()
