import pathlib,json,unreal as ue
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));client=next(w for w in ws if not ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();pawn=next(p for p in ue.GameplayStatics.get_all_actors_of_class(client,C) if p.is_locally_controlled())
pawn.get_component_by_class(ue.SpringArmComponent).target_arm_length=0
altar=ue.GameplayStatics.get_all_actors_with_tag(client,'Altar')[0];dest=altar.get_actor_location();dest.z+=105
pawn.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(pawn.get_component_by_class(ue.CameraComponent).get_world_location(),dest))
path=HERE/'altar-contact.png';ue.SystemLibrary.execute_console_command(client,'HighResShot 1 filename="'+path.as_posix()+'"',pawn.get_controller())
RESULT={'image_requested':str(path),'client_world':client.get_path_name(),'completed':altar.get_editor_property('Completed'),'key':str(altar.get_editor_property('PlacedKey'))}
