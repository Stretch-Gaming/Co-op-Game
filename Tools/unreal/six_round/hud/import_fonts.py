"""Import the unmodified, OFL-licensed font files with their embedded font faces."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from authoring import *
guard()
tools = ue.AssetToolsHelpers.get_asset_tools()
folder = '/Game/Shared/UI/Fonts'
faces = {}
for style in ('Regular', 'Bold'):
    name = 'FF_AveriaSerifLibre_' + style
    path = folder + '/' + name
    face = ue.load_asset(path)
    if not face:
        task = ue.AssetImportTask()
        task.set_editor_properties({'filename': str(ROOT/'SourceArt/HC/SixRoundUI/Fonts'/('AveriaSerifLibre-'+style+'.ttf')),
                                    'destination_path': folder, 'destination_name': name,
                                    'automated': True, 'replace_existing': False, 'save': True,
                                    'factory': ue.FontFileImportFactory()})
        tools.import_asset_tasks([task])
        face = ue.load_asset(path)
    assert isinstance(face, ue.FontFace), path
    faces[style] = face
fonts = {}
for style, face in faces.items():
    name = 'F_AveriaSerifLibre_' + style
    font = ue.load_asset(folder+'/'+name) or tools.create_asset(name, folder, ue.Font, ue.FontFactory())
    assert font
    font.set_editor_property('font_cache_type', ue.FontCacheType.RUNTIME)
    composite = ue.CompositeFont()
    text = '(DefaultTypeface=(Fonts=((Name="Regular",Font=(FontFaceAsset="/Script/Engine.FontFace\''+face.get_path_name()+'\'")))))'
    composite.import_text(text)
    assert face.get_path_name() in composite.export_text()
    font.set_editor_property('composite_font', composite)
    assert ue.EditorAssetLibrary.save_loaded_asset(font, False)
    fonts[style] = font.get_path_name()
RESULT = {'fonts': fonts, 'source': 'SourceArt/HC/SixRoundUI/Fonts', 'license': 'SIL OFL 1.1', 'visual_gate_pending': True}
