import unreal as ue
mat=ue.load_asset('/Game/Player/Art/M_Ghost')
RESULT={'methods':[n for n in dir(ue.MaterialEditingLibrary) if 'parameter' in n and 'names' in n], 'expressions':[{'name':o.get_name(),'class':o.get_class().get_name()} for o in ue.ObjectIterator(ue.MaterialExpression) if o.get_outer()==mat]}
RESULT['parameters']={str(o.get_editor_property('parameter_name')):o.get_editor_property('default_value') for o in ue.ObjectIterator(ue.MaterialExpressionScalarParameter) if o.get_outer()==mat}

