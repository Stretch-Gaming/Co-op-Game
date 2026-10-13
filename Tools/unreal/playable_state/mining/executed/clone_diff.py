"""Root inspection of partial UNSAVED clone stage. No edits or saves."""
import json,hashlib,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.object import ObjectTools as OBJ
OUT=Path('/tmp/coop-mining');ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
SOURCE='/Game/Hazards/L_Site01_HZ';HZ='/Game/Hazards/Test/SixRound/L_WorldRoute_Test'

def names(bp):
    result=[]
    while bp:
        result.extend(str(n) for n in BP.list_variables(bp))
        bp=ue.BlueprintEditorLibrary.get_blueprint_asset(BP.get_parent(bp))
    return sorted(set(result))

def properties(a):
    bp=ue.BlueprintEditorLibrary.get_blueprint_asset(a.get_class())
    return json.loads(OBJ.get_properties(a,names(bp)))

def remap(v,mapping):
    if isinstance(v,str):
        for src,dst in sorted(mapping.items(),key=lambda p:-len(p[0])):v=v.replace(src,dst)
        return v
    if isinstance(v,list):return [remap(x,mapping) for x in v]
    if isinstance(v,dict):return {k:remap(x,mapping) for k,x in v.items()}
    return v

def run():
    assert Path(ue.Paths.project_dir()).resolve()==ROOT
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    inventory=json.loads((OUT/'inventory.json').read_text())
    ue.load_asset(SOURCE)
    sources={a.get_path_name():a for a in ue.ObjectIterator(ue.Actor)
             if a.get_level() and a.get_level().get_outermost().get_name()==SOURCE}
    clones=[a for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors() if a.actor_has_tag('SixRoundMining')]
    assert len(clones)==len(inventory['source_actors'])==11
    assert all(a.get_level().get_outermost().get_name()==HZ for a in clones)
    mapping={};actor_mapping={}
    for row in inventory['source_actors']:
        src=sources[row['path']]
        matches=[a for a in clones if a.get_class()==src.get_class() and (a.get_actor_location()-src.get_actor_location()).length()<.01]
        assert len(matches)==1,(src.get_path_name(),len(matches))
        mapping[src.get_path_name()]=matches[0].get_path_name();actor_mapping[src.get_path_name()]=matches[0]
    report={'inspection_only':True,'mapping':mapping,'actors':[],'protected_sha256':inventory['protected_sha256']}
    for row in inventory['source_actors']:
        src=sources[row['path']];clone=actor_mapping[row['path']]
        before=properties(src);actual=properties(clone);expected=remap(before,mapping)
        diffs=[{'field':n,'expected':expected.get(n),'actual':actual.get(n)} for n in sorted(set(expected)|set(actual)) if expected.get(n)!=actual.get(n)]
        baseline={n:v[n] for n,v in row['variables'].items() if n in v}
        source_baseline_diff=[n for n in baseline if before.get(n)!=baseline[n]]
        report['actors'].append({'source':src.get_path_name(),'clone':clone.get_path_name(),
              'class':clone.get_class().get_name(),'source_properties':before,'expected':expected,'actual':actual,
              'differences':diffs,'source_baseline_diff':source_baseline_diff,
              'source_transform':src.get_actor_transform().export_text(),'clone_transform':clone.get_actor_transform().export_text()})
        (OUT/'clone-diff-partial.json').write_text(json.dumps(report,indent=2))
    report['protected_bytes_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in report['protected_sha256'].items())
    assert report['protected_bytes_unchanged']
    (OUT/'clone-diff.json').write_text(json.dumps(report,indent=2))
    return report

try:
    RESULT=run();print('COOP_MINING clone diff: '+str(OUT/'clone-diff.json'))
except Exception:
    (OUT/'clone-diff-error.json').write_text(json.dumps({'error':traceback.format_exc()},indent=2));raise
