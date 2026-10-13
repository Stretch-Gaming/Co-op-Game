"""Read-only queue diagnostic; allowed during PIE, never changes inputs/state."""
import sys,json
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
registry=sys.modules.get('coop_mining_completion')
state=getattr(registry,'state',{}) if registry else {}
RESULT={'pie_worlds':[w.get_path_name() for w in worlds],
 'mining':{k:state.get(k) for k in ('phase','case','players','passed','error','checks','first_health_loss')},
 'mining_callback_active':bool(getattr(registry,'handle',None)) if registry else False}
