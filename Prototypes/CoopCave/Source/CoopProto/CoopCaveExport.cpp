#include "CoopPlayground.h"

#include "Components/BoxComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "ProceduralMeshComponent.h"
#include "PhysicsEngine/BodySetup.h"
#include "Serialization/JsonSerializer.h"

namespace CoopCaveTransfer
{
	TArray<TSharedPtr<FJsonValue>> Numbers(std::initializer_list<double> Values)
	{
		TArray<TSharedPtr<FJsonValue>> Result;
		for (double Value : Values) { Result.Add(MakeShared<FJsonValueNumber>(Value)); }
		return Result;
	}

	TSharedPtr<FJsonObject> ComponentRecord(USceneComponent* Component)
	{
		TSharedPtr<FJsonObject> Record = MakeShared<FJsonObject>();
		const FTransform Transform = Component->GetComponentTransform();
		const FVector P = Transform.GetLocation();
		const FRotator R = Transform.Rotator();
		const FVector S = Transform.GetScale3D();
		Record->SetStringField(TEXT("name"), Component->GetName());
		Record->SetArrayField(TEXT("location"), Numbers({P.X, P.Y, P.Z}));
		Record->SetArrayField(TEXT("rotation"), Numbers({R.Pitch, R.Yaw, R.Roll}));
		Record->SetArrayField(TEXT("scale"), Numbers({S.X, S.Y, S.Z}));
		return Record;
	}

	void AddMaterial(UMeshComponent* Component, TSharedPtr<FJsonObject> Record)
	{
		FLinearColor Color = FLinearColor::White;
		UMaterialInterface* Material = Component->GetMaterial(0);
		if (UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Material))
		{
			Color = Dynamic->K2_GetVectorParameterValue(TEXT("Color"));
		}
		Record->SetArrayField(TEXT("color"), Numbers({Color.R, Color.G, Color.B, Color.A}));
		Record->SetBoolField(TEXT("glow"), Material && Material->GetName().Contains(TEXT("VertexColor")));
		Record->SetBoolField(TEXT("collision"), Component->GetCollisionEnabled() != ECollisionEnabled::NoCollision);
		Record->SetBoolField(TEXT("shadow"), Component->CastShadow);
		Record->SetBoolField(TEXT("visible"), Component->IsVisible() && !Component->bHiddenInGame);
		if (Material)
		{
			FLinearColor Tint;
			if (Material->GetVectorParameterValue(FMaterialParameterInfo(TEXT("Tint")), Tint))
			{
				Record->SetArrayField(TEXT("tint"), Numbers({Tint.R, Tint.G, Tint.B, Tint.A}));
			}
			if (!Material->IsA<UMaterialInstanceDynamic>())
			{
				Record->SetStringField(TEXT("material"), Material->GetPathName());
			}
		}
	}

	void AddConvexCollision(UProceduralMeshComponent* Component, TSharedPtr<FJsonObject> Record)
	{
		TArray<TSharedPtr<FJsonValue>> Hulls;
		if (UBodySetup* Body = Component->GetBodySetup())
		{
			for (const FKConvexElem& Hull : Body->AggGeom.ConvexElems)
			{
				TArray<TSharedPtr<FJsonValue>> Points;
				for (const FVector& Vertex : Hull.VertexData)
				{
					const FVector P = Hull.GetTransform().TransformPosition(Vertex);
					Points.Add(MakeShared<FJsonValueArray>(Numbers({P.X, P.Y, P.Z})));
				}
				Hulls.Add(MakeShared<FJsonValueArray>(Points));
			}
		}
		Record->SetArrayField(TEXT("convex_hulls"), Hulls);
	}

	void Export(UWorld* World)
	{
		TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Records, Stations, Movers;
		for (TActorIterator<ACoopPlayground> It(World); It; ++It)
		{
			for (const FCoopStation& Station : It->GetStations())
			{
				TSharedPtr<FJsonObject> Data = MakeShared<FJsonObject>();
				Data->SetStringField(TEXT("name"), Station.Name);
				Data->SetStringField(TEXT("description"), Station.Status);
				Data->SetArrayField(TEXT("location"), Numbers({Station.Location.X, Station.Location.Y, Station.Location.Z}));
				Data->SetNumberField(TEXT("yaw"), Station.Yaw);
				Stations.Add(MakeShared<FJsonValueObject>(Data));
			}
			TSet<USceneComponent*> MovingPieces;
			for (const FCoopMover& Mover : It->GetTransferMovers())
			{
				UStaticMeshComponent* Piece = It->GetTransferMoverPiece(Mover.Piece);
				if (!Piece) { continue; }
				MovingPieces.Add(Piece);
				TSharedPtr<FJsonObject> Data = ComponentRecord(Piece);
				Data->SetArrayField(TEXT("rest"), Numbers({Mover.RestLocation.X, Mover.RestLocation.Y, Mover.RestLocation.Z}));
				Data->SetArrayField(TEXT("active"), Numbers({Mover.ActiveLocation.X, Mover.ActiveLocation.Y, Mover.ActiveLocation.Z}));
				Data->SetBoolField(TEXT("needs_brace"), Mover.bNeedsBrace);
				Data->SetBoolField(TEXT("gate"), Mover.bGate);
				TArray<TSharedPtr<FJsonValue>> Plates;
				for (const FBox& Plate : Mover.Plates)
				{
					TSharedPtr<FJsonObject> Box = MakeShared<FJsonObject>();
					Box->SetArrayField(TEXT("min"), Numbers({Plate.Min.X, Plate.Min.Y, Plate.Min.Z}));
					Box->SetArrayField(TEXT("max"), Numbers({Plate.Max.X, Plate.Max.Y, Plate.Max.Z}));
					Plates.Add(MakeShared<FJsonValueObject>(Box));
				}
				Data->SetArrayField(TEXT("plates"), Plates);
				Data->SetBoolField(TEXT("keep_open_valid"), Mover.KeepOpen.IsValid != 0);
				if (Mover.KeepOpen.IsValid)
				{
					Data->SetArrayField(TEXT("keep_open_min"), Numbers({Mover.KeepOpen.Min.X, Mover.KeepOpen.Min.Y, Mover.KeepOpen.Min.Z}));
					Data->SetArrayField(TEXT("keep_open_max"), Numbers({Mover.KeepOpen.Max.X, Mover.KeepOpen.Max.Y, Mover.KeepOpen.Max.Z}));
				}
				AddMaterial(Piece, Data);
				Movers.Add(MakeShared<FJsonValueObject>(Data));
			}
			TArray<USceneComponent*> Components;
			It->GetComponents<USceneComponent>(Components);
			for (USceneComponent* Component : Components)
			{
				if (MovingPieces.Contains(Component)) { continue; }
				TSharedPtr<FJsonObject> Record = ComponentRecord(Component);
				if (UStaticMeshComponent* Static = Cast<UStaticMeshComponent>(Component))
				{
					if (!Static->GetStaticMesh()) { continue; }
					Record->SetStringField(TEXT("kind"), Static->IsA<UInstancedStaticMeshComponent>() ? TEXT("instanced") : TEXT("static"));
					Record->SetStringField(TEXT("mesh"), Static->GetStaticMesh()->GetPathName());
					AddMaterial(Static, Record);
					if (UInstancedStaticMeshComponent* Instanced = Cast<UInstancedStaticMeshComponent>(Static))
					{
						TArray<TSharedPtr<FJsonValue>> Instances;
						for (int32 Index = 0; Index < Instanced->GetInstanceCount(); ++Index)
						{
							FTransform Transform;
							Instanced->GetInstanceTransform(Index, Transform, true);
							const FVector P = Transform.GetLocation();
							const FRotator R = Transform.Rotator();
							const FVector S = Transform.GetScale3D();
							TSharedPtr<FJsonObject> Data = MakeShared<FJsonObject>();
							Data->SetArrayField(TEXT("location"), Numbers({P.X, P.Y, P.Z}));
							Data->SetArrayField(TEXT("rotation"), Numbers({R.Pitch, R.Yaw, R.Roll}));
							Data->SetArrayField(TEXT("scale"), Numbers({S.X, S.Y, S.Z}));
							Instances.Add(MakeShared<FJsonValueObject>(Data));
						}
						Record->SetArrayField(TEXT("instances"), Instances);
					}
				}
				else if (UProceduralMeshComponent* Proc = Cast<UProceduralMeshComponent>(Component))
				{
					const FProcMeshSection* Section = Proc->GetProcMeshSection(0);
					Record->SetStringField(TEXT("kind"), Section ? TEXT("procedural") : TEXT("collision"));
					AddMaterial(Proc, Record);
					AddConvexCollision(Proc, Record);
					if (!Section)
					{
						if (!Record->GetArrayField(TEXT("convex_hulls")).IsEmpty()) { Records.Add(MakeShared<FJsonValueObject>(Record)); }
						continue;
					}
					TArray<TSharedPtr<FJsonValue>> Vertices, Normals, UVs, Colors, Triangles;
					for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
					{
						Vertices.Add(MakeShared<FJsonValueArray>(Numbers({Vertex.Position.X, Vertex.Position.Y, Vertex.Position.Z})));
						Normals.Add(MakeShared<FJsonValueArray>(Numbers({Vertex.Normal.X, Vertex.Normal.Y, Vertex.Normal.Z})));
						UVs.Add(MakeShared<FJsonValueArray>(Numbers({Vertex.UV0.X, Vertex.UV0.Y})));
						const FLinearColor C = FLinearColor::FromSRGBColor(Vertex.Color);
						Colors.Add(MakeShared<FJsonValueArray>(Numbers({C.R, C.G, C.B, C.A})));
					}
					for (uint32 Index : Section->ProcIndexBuffer) { Triangles.Add(MakeShared<FJsonValueNumber>(Index)); }
					Record->SetArrayField(TEXT("vertices"), Vertices);
					Record->SetArrayField(TEXT("normals"), Normals);
					Record->SetArrayField(TEXT("uvs"), UVs);
					Record->SetArrayField(TEXT("vertex_colors"), Colors);
					Record->SetArrayField(TEXT("triangles"), Triangles);
				}
				else if (UBoxComponent* Box = Cast<UBoxComponent>(Component))
				{
					Record->SetStringField(TEXT("kind"), TEXT("blocker"));
					const FVector Extent = Box->GetUnscaledBoxExtent();
					Record->SetArrayField(TEXT("extent"), Numbers({Extent.X, Extent.Y, Extent.Z}));
				}
				else if (UPointLightComponent* Light = Cast<UPointLightComponent>(Component))
				{
					Record->SetStringField(TEXT("kind"), TEXT("point"));
					Record->SetNumberField(TEXT("intensity"), Light->Intensity);
					Record->SetNumberField(TEXT("radius"), Light->AttenuationRadius);
					Record->SetBoolField(TEXT("shadow"), Light->CastShadows);
					const FLinearColor C = Light->GetLightColor();
					Record->SetArrayField(TEXT("color"), Numbers({C.R, C.G, C.B, C.A}));
				}
				else { continue; }
				Records.Add(MakeShared<FJsonValueObject>(Record));
			}
		}
		Root->SetArrayField(TEXT("components"), Records);
		Root->SetArrayField(TEXT("stations"), Stations);
		Root->SetArrayField(TEXT("movers"), Movers);
		Root->SetNumberField(TEXT("version"), 2);
		Root->SetStringField(TEXT("maze_detail_reference"), TEXT("PR #90, with subsequent reviewed co-op/style fixes"));
		Root->SetNumberField(TEXT("seed"), 2610);
		Root->SetStringField(TEXT("source"), TEXT("CoopCave procedural environment only; no character or gameplay code"));
		FString Json;
		FJsonSerializer::Serialize(Root.ToSharedRef(), TJsonWriterFactory<>::Create(&Json));
		const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("CaveTransfer"));
		IFileManager::Get().MakeDirectory(*Directory, true);
		const FString Filename = FPaths::Combine(Directory, TEXT("cave.json"));
		if (!Records.IsEmpty() && FFileHelper::SaveStringToFile(Json, *Filename, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
		{
			UE_LOG(LogTemp, Display, TEXT("CAVE_EXPORT_COMPLETE: %d components to %s"), Records.Num(), *Filename);
		}
		else { UE_LOG(LogTemp, Error, TEXT("Cave export failed or no playground was loaded")); }
	}

	FAutoConsoleCommandWithWorld Command(TEXT("coop.ExportCave"), TEXT("Export cave geometry and lights for editor baking into CoopGame."), FConsoleCommandWithWorldDelegate::CreateStatic(&Export));
}
