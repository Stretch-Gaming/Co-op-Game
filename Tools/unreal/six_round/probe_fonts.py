"""Inspect factory and struct support before importing licensed fonts."""
import unreal as ue
RESULT = {'types': [n for n in dir(ue) if any(s in n for s in ('Typeface', 'FontData', 'FontFace', 'FontOutline', 'FontCache'))],
          'font_properties': [n for n in dir(ue.Font) if 'font' in n.lower()]}
for name in ('FontFactory', 'FontFileImportFactory', 'TrueTypeFontFactory'):
    factory = getattr(ue, name)()
    RESULT[name] = {'supported_class': str(factory.get_editor_property('supported_class')),
                    'doc': getattr(ue, name).__doc__}
