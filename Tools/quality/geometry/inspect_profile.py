import unreal as ue
character=ue.get_default_object(ue.EditorAssetLibrary.load_blueprint_class('/Game/Core/BP_CoopCharacter'))
capsule=character.get_component_by_class(ue.CapsuleComponent)
channels=['ECC_WORLD_STATIC','ECC_WORLD_DYNAMIC','ECC_PAWN','ECC_VISIBILITY','ECC_CAMERA','ECC_PHYSICS_BODY','ECC_VEHICLE','ECC_DESTRUCTIBLE']
RESULT={'profile':str(capsule.get_collision_profile_name()),'object_type':str(capsule.get_collision_object_type()),'responses':{n:str(capsule.get_collision_response_to_channel(getattr(ue.CollisionChannel,n)))for n in channels}}
