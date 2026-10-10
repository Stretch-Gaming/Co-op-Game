import sys,pathlib,importlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import authoring;importlib.reload(authoring)
from authoring import *
bp=unreal.load_asset('/Game/Puzzles/BP_Altar');V=lambda n:f'(Variables|Default|Get{n})';S=lambda n,v:f'(Variables|Default|Set{n} {v})'
source=pathlib.Path(__file__).parent.joinpath('build.py').read_text(encoding='utf-8-sig')
exec(source[source.index("write(bp,'CanAccept'"):source.index("write(bp,'CanInteract'")])
component(bp,'AltarSocket',unreal.SceneComponent.static_class()).set_editor_property('relative_location',unreal.Vector(0,0,125.305))
save(bp)
RESULT={'validates_stale_carried':True,'socket_default_height':125.305}
