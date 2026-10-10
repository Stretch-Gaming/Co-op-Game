import unreal as ue
font = ue.load_asset('/Engine/EngineFonts/Roboto')
composite = font.get_editor_property('composite_font')
RESULT = {'cache_type': str(font.get_editor_property('font_cache_type')), 'composite': composite.export_text()}
(QUEUE/'font-composite.json').write_text(__import__('json').dumps(RESULT, indent=2))
