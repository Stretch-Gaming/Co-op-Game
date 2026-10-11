import unreal as ue
RESULT={'methods':[n for n in dir(ue) if 'ModelContext' in n],'editor_exec':[n for n in dir(ue.EditorLevelLibrary) if 'exec' in n or 'play' in n]}
