import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
from editor_toolset.toolsets.object import ObjectTools as OBJ
guard()
config=json.loads((OUT/'run-config.json').read_text())
assert config['players'] in (2,3,4)
unreal.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings').set_editor_property('bThrottleCPUWhenNotForeground',False)
settings=unreal.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
OBJ.set_properties(settings,json.dumps({'PlayNetMode':'PIE_ListenServer' if config.get('split') else 'PIE_Client',
 'PlayNumberOfClients':config['players']-1 if config.get('split') else config['players'],'RunUnderOneProcess':True}))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Puzzles/Test/HC6/L_HC6_Round1')
(OUT/'pie-settings.json').write_text(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
