import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
from editor_toolset.toolsets.object import ObjectTools as OBJ
guard()
settings=unreal.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_Client','PlayNumberOfClients':2,'RunUnderOneProcess':True}))
unreal.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings').set_editor_property('bThrottleCPUWhenNotForeground',False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/L_Site01')
