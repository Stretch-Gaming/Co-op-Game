"""Read-only progress of the active transaction suite."""
import sys
r=sys.modules.get('six_round_core_test_registry')
s=getattr(r,'suite',None) if r else None
RESULT={'active':bool(r and getattr(r,'handle',None))}
if s:
    RESULT.update(phase=s.phase,check_count=len(s.checks),last_checks=s.checks[-2:],action_injections=getattr(s,'action_injections',[])[-3:],round=s.rt.round(),elapsed=s.elapsed(),players=[{'id':p.player_state.player_id,'dead':s.rt.dead(i),'location':[p.get_actor_location().x,p.get_actor_location().y,p.get_actor_location().z],'carried':s.rt.carried(i).get_name() if s.rt.carried(i) else None} for i,p in enumerate(s.rt.players)])
