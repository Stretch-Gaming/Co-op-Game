import unreal as ue
w=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
hit=ue.SystemLibrary.line_trace_single(w,ue.Vector(325,2300,125),ue.Vector(325,2300,-600),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],ue.DrawDebugTrace.NONE,True)
RESULT={'line_doc':ue.SystemLibrary.line_trace_single.__doc__,'capsule_doc':ue.SystemLibrary.capsule_trace_single.__doc__,'result':str(hit),'fields':dir(hit) if hit else []}
if hit:RESULT['dictionary']={key:str(value) for key,value in hit.to_dict().items()}
