import sys
import unreal as ue
r=sys.modules.get('six_round_core_test_registry');s=getattr(r,'suite',None)
RESULT={'phase':s.phase,'checks':len(s.checks),'round':s.rt.round(),'run':s.run_number,
        'players':[{'dead':s.rt.dead(i),'position':str(p.get_actor_location())} for i,p in enumerate(s.rt.players)]} if s else None
if s:
    RESULT['locks']=[]
    for a in ue.GameplayStatics.get_all_actors_of_class(s.rt.server,ue.load_asset('/Game/Puzzles/BP_CrystalLock').generated_class()):
        row={'label':a.get_actor_label(),'position':str(a.get_actor_location())}
        for key in ('Enabled','Lit','Brazier','RequiredRound'):
            try:row[key]=str(a.get_editor_property(key))
            except Exception:pass
        RESULT['locks'].append(row)
    RESULT['flares']=[str(a.get_actor_location()) for a in ue.GameplayStatics.get_all_actors_of_class(s.rt.server,ue.load_asset('/Game/Player/Tools/BP_Flare').generated_class())]
    RESULT['beam']=[{'target':str(p.get_component_by_class(s.rt.TOOLS).get_editor_property('BeamTarget'))} for p in s.rt.players]
