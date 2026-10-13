"""Root-only bounded editor stage. Requires reviewed inventory and own lease.

ARGS = {'execute': True, 'lease_owner': '<actual GitHub lock owner>',
        'remove_static_cart': '<exact derivative actor path or empty>'}
Root writes /tmp/coop-mining/leases.json from current git lfs locks --json.
No source map, persistent map or Blueprint is saved by this stage.
"""
import json,hashlib,re
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.object import ObjectTools as OBJ

OUT=Path('/tmp/coop-mining')
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
SOURCE='/Game/Hazards/L_Site01_HZ'
PERSISTENT='/Game/Puzzles/Test/SixRound/L_SixRound_Test'
HZ='/Game/Hazards/Test/SixRound/L_WorldRoute_Test'
HC='/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test'
CAVE='/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test'
stage={'name':'preflight','saved':[]}
def run_placement():
    args=globals().get('ARGS',{})
    assert args.get('execute') is True, 'Root must explicitly select the mutation stage'
    assert Path(ue.Paths.project_dir()).resolve()==ROOT
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    inventory=json.loads((OUT/'inventory.json').read_text())
    assert inventory['inspection_only'] and inventory['editor_world']==PERSISTENT
    leases=json.loads((OUT/'leases.json').read_text())
    lease_rows=leases.get('locks',[]) if isinstance(leases,dict) else leases
    lease_path='Content/Hazards/Test/SixRound/L_WorldRoute_Test.umap'
    assert any(r['path']==lease_path and r.get('owner',{}).get('name')==args['lease_owner'] for r in lease_rows), 'Exact own HZ derivative lease required'
    protected=inventory['protected_sha256']
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()), 'Protected source bytes changed since inspection'
    editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
    actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
    world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_name()==PERSISTENT
    streams={p:ue.GameplayStatics.get_streaming_level(world,p.rsplit('/',1)[-1]) for p in (HZ,HC,CAVE)}
    assert all(s and s.get_loaded_level().get_outermost().get_name()==p for p,s in streams.items())
    source=ue.load_asset(SOURCE);assert source
    source_by_path={a.get_path_name():a for a in ue.ObjectIterator(ue.Actor)
                    if a.get_level() and a.get_level().get_outermost().get_name()==SOURCE}
    selected=[source_by_path[x['path']] for x in inventory['source_actors']]
    counts={name:sum(a.get_class().get_name()==name for a in selected) for name in
     ('BP_MinePuzzle_C','BP_MineCart_C','BP_MinePickaxe_C','BP_MineDeposit_C','BP_PressurePlate_C')}
    assert counts=={'BP_MinePuzzle_C':1,'BP_MineCart_C':1,'BP_MinePickaxe_C':1,'BP_MineDeposit_C':4,'BP_PressurePlate_C':4}, counts
    current=list(actors.get_all_level_actors())
    assert not any(a.actor_has_tag('SixRoundMining') or a.get_class().get_name().startswith('BP_Mine') for a in current), 'Refuse duplicate mining placement'
    old=[a for a in current if a.get_level().get_outermost().get_name()==HC and
         (a.get_actor_label()=='Six_PlatePuzzle' or a.get_actor_label() in {'Six_Plate_'+str(i) for i in range(4)})]
    assert len(old)==5, [(a.get_actor_label(),a.get_class().get_name()) for a in old]
    assert sum(a.get_class().get_name()=='BP_PuzzleSetup_C' for a in old)==1
    assert sum(a.get_class().get_name()=='BP_PressurePlate_C' for a in old)==4
    preserved={a.get_path_name():(a.get_class().get_path_name(),a.get_actor_transform().export_text(),[str(t) for t in a.tags])
               for a in current if a not in old}
    cart_path=args.get('remove_static_cart','')
    cart=None
    if cart_path:
        cart=next((a for a in current if a.get_path_name()==cart_path),None)
        assert cart and cart.get_level().get_outermost().get_name()==CAVE
        assert isinstance(cart,ue.StaticMeshActor), 'Only the reviewed decorative mesh may be removed'
        assert 'cart' in cart.get_actor_label().lower()
        del preserved[cart_path]
    
    def inherited_vars(bp):
        names=[]
        while bp:
            names.extend(str(n) for n in BP.list_variables(bp))
            bp=ue.BlueprintEditorLibrary.get_blueprint_asset(BP.get_parent(bp))
        return sorted(set(names))
    
    def refs(a):
        bp=ue.BlueprintEditorLibrary.get_blueprint_asset(a.get_class())
        names=inherited_vars(bp) if bp else []
        return json.loads(OBJ.get_properties(a,names))
    
    def string_leaves(value):
        if isinstance(value,str):yield value
        elif isinstance(value,dict):
            for v in value.values():yield from string_leaves(v)
        elif isinstance(value,list):
            for v in value:yield from string_leaves(v)
    
    source_properties={a.get_path_name():refs(a) for a in selected}
    
    # Native duplicate API routes a same-source-level batch through copy/paste,
    # preserving instance settings and remapping intra-batch actor references.
    ue.EditorLevelUtils.make_level_current(streams[HZ])
    stage["name"]="before_duplicate"
    (OUT/"placement-partial.json").write_text(json.dumps(stage,indent=2))
    clones=list(actors.duplicate_actors(selected,world,ue.Vector()))
    stage["name"]="clones_created"
    stage["clones"]=[a.get_path_name() for a in clones]
    (OUT/"placement-partial.json").write_text(json.dumps(stage,indent=2))
    assert len(clones)==len(selected)
    clone_counts={name:sum(a.get_class().get_name()==name for a in clones) for name in counts}
    assert clone_counts==counts
    assert all(a.get_level().get_outermost().get_name()==HZ for a in clones)
    clone_map={}
    for a in clones:
        src=[s for s in selected if s.get_class()==a.get_class() and
             (s.get_actor_location()-a.get_actor_location()).length()<0.1]
        assert len(src)==1, 'Duplicate source matching is ambiguous'
        assert (src[0].get_actor_scale3d()-a.get_actor_scale3d()).length()<0.0001
        delta=ue.MathLibrary.normalized_delta_rotator(src[0].get_actor_rotation(),a.get_actor_rotation())
        assert max(abs(delta.pitch),abs(delta.yaw),abs(delta.roll))<0.01
        clone_map[src[0].get_path_name()]=a
        a.set_actor_label('Six_'+src[0].get_actor_label())
        a.tags=list(a.tags)+[ue.Name('SixRoundMining')]
    assert len(clone_map)==len(selected)
    # Native batch duplication was observed to scramble only the puzzle's deposit
    # array. Rewire that array from the original typed array through the exact
    # source→clone identity map before comparing every instance field.
    for source_path,a in clone_map.items():
        if a.get_class().get_name()=='BP_MinePuzzle_C':
            source_puzzle=source_by_path[source_path]
            source_deposits=list(source_puzzle.get_editor_property('Deposits'))
            assert len(source_deposits)==4 and len({d.get_editor_property('Slot') for d in source_deposits})==4
            linked=[clone_map[d.get_path_name()] for d in source_deposits]
            assert all(d.get_level()==a.get_level() for d in linked)
            a.set_editor_property('Deposits',linked)
    for source_path,a in clone_map.items():
        expected=json.dumps(source_properties[source_path],sort_keys=True)
        # Actor and component reference paths are remapped together. Exact property
        # comparison proves required links weren't cleared to None by copy/paste.
        for old_path,new_actor in sorted(clone_map.items(),key=lambda x:-len(x[0])):
            expected=expected.replace(old_path,new_actor.get_path_name())
        actual=refs(a)
        assert json.loads(expected)==actual, 'Cloned Blueprint instance properties or reference links changed: '+source_path
        for text in string_leaves(actual):
            for match in re.findall(r'(/Game/[^\s\"\x27,()]*:PersistentLevel\.[^\s\"\x27,()]*)',text):
                assert match.startswith(HZ+'.'), 'Cross-sublevel placed reference: '+match
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    # Validate all new actors before retiring any old logic. Never run this stage
    # twice after a partial failure; root reviews the editor transaction first.
    stage["name"]="all_fields_and_links_match"
    (OUT/"placement-partial.json").write_text(json.dumps(stage,indent=2))
    removed=[]
    for a in old+([cart] if cart else []):
        removed.append(a.get_path_name());assert actors.destroy_actor(a)
    remaining={a.get_path_name():a for a in actors.get_all_level_actors()}
    for path,(cls,xform,tags) in preserved.items():
        a=remaining[path]
        assert (a.get_class().get_path_name(),a.get_actor_transform().export_text(),[str(t) for t in a.tags])==(cls,xform,tags), path
    assert sum(a.actor_has_tag('ConnectionDoor') for a in remaining.values())==1
    assert sum(a.get_actor_label()=='Six_StartPad' for a in remaining.values())==1
    packages=[streams[p].get_loaded_level().get_outermost() for p in ((HZ,HC,CAVE) if cart else (HZ,HC))]
    stage["name"]="old_actors_retired_before_save"
    stage["removed"]=removed
    (OUT/"placement-partial.json").write_text(json.dumps(stage,indent=2))
    assert ue.EditorLoadingAndSavingUtils.save_packages(packages,False)
    stage["name"]="exact_maps_saved"
    stage["saved"]=[p.get_name() for p in packages]
    (OUT/"placement-partial.json").write_text(json.dumps(stage,indent=2))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    RESULT={'stage':'bounded_mining_placement','source_read_only':SOURCE,
            'saved':[p.get_name() for p in packages],'removed':removed,
            'clones':[{'path':a.get_path_name(),'label':a.get_actor_label(),'class':a.get_class().get_name(),
                       'transform':a.get_actor_transform().export_text(),'references':refs(a)} for a in clones],
            'unrelated_actor_count_preserved':len(preserved),'gameplay_acceptance_pending':True}
    RESULT['passed']=True
    (OUT/'placement.json').write_text(json.dumps(RESULT,indent=2))
    (OUT/'placement-finalized.json').write_text(json.dumps(RESULT,indent=2))
    print('COOP_MINING placement: '+str(OUT/'placement.json'))
    return RESULT

try:
    RESULT=run_placement()
except Exception:
    import traceback
    stage.update(passed=False,error=traceback.format_exc())
    try:
        stage['current_clones']=[a.get_path_name() for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors() if a.actor_has_tag('SixRoundMining')]
    except Exception:pass
    (OUT/'placement-error.json').write_text(json.dumps(stage,indent=2))
    raise
