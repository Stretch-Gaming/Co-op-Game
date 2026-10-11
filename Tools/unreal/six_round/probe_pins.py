"""Inspect exposed editor APIs for parameter/root-component operations."""
import unreal as ue
RESULT = {'graph': [x for x in dir(ue.BlueprintGraphEditor) if any(t in x.lower() for t in ('pin', 'event', 'param'))],
          'subobject': [x for x in dir(ue.SubobjectDataSubsystem) if any(t in x.lower() for t in ('root', 'attach'))],
          'custom_event': [x for x in dir(ue.K2Node_CustomEvent) if any(t in x.lower() for t in ('pin', 'param'))]}
RESULT['make_root_doc'] = ue.SubobjectDataSubsystem.make_new_scene_root.__doc__
RESULT['event_doc'] = ue.BlueprintGraphEditor.add_custom_event_node.__doc__
RESULT['input_doc'] = ue.BlueprintGraphEditor.add_graph_input_parameter.__doc__
RESULT['fonts'] = [n for n in dir(ue) if 'Font' in n and ('Factory' in n or n in ('CompositeFont','TypefaceEntry','FontData'))]
